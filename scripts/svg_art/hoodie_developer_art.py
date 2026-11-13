#!/usr/bin/env python3
"""How the hoodie developer's SVG was first drawn (reference, not authority).

    uv run python scripts/svg_art/hoodie_developer_art.py

Writes ``data/characters/hoodie_developer/hoodie_developer.svg``; the SVG owns the
art after this has run once. ``joints()`` says where each part turns and
``LAYERS`` lists the parts; ``scripts/build_hoodie_developer_rig.py`` reads both
and authors the rows.

Who he is: a developer, not a wizard: a charcoal hoodie with its hood down,
jeans and sneakers, glasses, a gaming headset with a boom mic. He carries a
mechanical keyboard on a strap like a keytar. No character wears him yet; the
final boss is the Director (``director_boss_art.py``), who borrowed the
keyboard. He is not the Creator of the intro (the robot's maker); he is drawn
on the Creator's skeleton and parts (``creator_art``), so the two are the same
build of man and the rows have the same bones.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Dict, Tuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _cel_profile_kit as K  # noqa: E402
from _cel_profile_kit import capsule, cel, ellipse, hd, lerp, line, path, smooth  # noqa: E402

_spec = importlib.util.spec_from_file_location("creator_art", HERE / "creator_art.py")
C = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C)

ROOT = HERE.parents[1]
OUT = ROOT / "ambition_sprite2d_renderer" / "data" / "characters" / "hoodie_developer" / "hoodie_developer.svg"
VIEW = "hoodie_developer - Side Right"
OW = 1.5
GROUND_Y = C.GROUND_Y
BONES = C.BONES

LOOK = dict(
    ink="#16141a", skin="#d6a386", skin_sh="#a8775f", skin_lt="#ecc2a6",
    hair="#3a2a22", hair_lt="#5c463a", grey="#3a2a22", stubble="#4a3a30",
    # the hoodie
    coat="#2e3038", coat_sh="#1d1e24", coat_lt="#474a56", shirt="#2e3038", shirt_sh="#1d1e24", shirt_lt="#474a56",
    accent="#d23c3c", accent_sh="#962626",
    legs="#3a4a6a", legs_sh="#283450", legs_lt="#56688e",
    shoe="#e8e4dc", shoe_sh="#b4aea4", shoe_lt="#ffffff", sole="#d23c3c",
    glasses=("#141214", 2.2), hair_kind="short", beard="stubble", prop="keyboard", build=(1.0, 1.0), belly=4,
    badge="#ffd23c", badge_glow="#fff2b0",
    gold="#f2c230", gold_sh="#c08a18", gold_lt="#fff0a0",
    key="#e6e2da", key_sh="#a8a29a", case="#26272e", case_sh="#141418",
)

#: Where the drawing's joints are. The far arm comes out of the pocket and
#: reaches the keyboard: both hands are on the keys.
J = dict(C.BASE_J)
J.update(far_elbow=(262.0, 290.0), far_wrist=(298.0, 300.0))


def joints() -> Dict[str, Tuple[float, float]]:
    return dict(J)


def hoodie(o):
    """The hoodie to the hip, its pocket, its drawstrings, the hood down on
    the back of the neck, and the keyboard's strap across the chest."""
    b = o["belly"]
    sil = smooth([(250, 212), (274, 204), (292, 212), (298, 240), (300 + b * 0.5, 280), (302 + b * 0.6, 336, True),
                  (240, 342, True), (236, 300), (238, 252), (242, 226)])
    items = [
        # the front pocket
        path(smooth([(258, 296, True), (296 + b * 0.5, 294, True), (298 + b * 0.6, 326, True), (258, 328, True)]), o["coat_sh"]),
        line([(260, 298), (294 + b * 0.5, 296)], o["coat_lt"], 1.4),
        # the waistband
        line([(242, 334), (301 + b * 0.6, 330)], o["coat_lt"], 2.0),
        # the drawstrings
        line([(284, 214), (286, 246)], o["accent"], 1.8),
        line([(290, 216), (293, 250)], o["accent"], 1.8),
    ]
    out = cel(sil, o["coat"], o["coat_sh"], o["coat_lt"], items, s=(10, -4))
    # the hood, down on the back of the neck
    hood = smooth([(246, 196), (262, 188), (276, 196), (272, 214), (256, 226), (242, 222)])
    out += cel(hood, o["coat"], o["coat_sh"], o["coat_lt"], [line([(250, 202), (268, 196)], o["coat_sh"], 1.2)], s=(4, -2))
    # the keyboard's strap, from the far shoulder across the chest to the near hip
    out.append(line([(262, 214), (282, 262), (302, 302)], K.INK, 6.0))
    out.append(line([(262, 214), (282, 262), (302, 302)], o["accent"], 3.6))
    return out


def head(o):
    """The Creator's head with short hair, stubble and glasses; the headset
    is a part of its own (``headset``)."""
    return C.head(o)


def headset(o):
    """The headset: band over the top, cup on the ear, boom mic to the mouth."""
    c, k = C.BASE_J["head"], C.HEAD_K
    out = []
    band = hd(c, k, [(-10, 4), (-14, -20), (-6, -42), (10, -46)])
    out.append(line(band, K.INK, 7.0))
    out.append(line(band, "#34343c", 4.0))
    cup = smooth(hd(c, k, [(-18, -4), (-4, -6), (-2, 14), (-16, 16)]))
    out += cel(cup, "#34343c", "#1c1c22", "#54545e", [ellipse(*hd(c, k, [(-10, 5)])[0], 3.6, 4.6, o["accent"])], s=(3, -2))
    mic = hd(c, k, [(-6, 12), (6, 24), (20, 28)])
    out.append(line(mic, K.INK, 3.6))
    out.append(line(mic, "#54545e", 1.8))
    out += cel(smooth(hd(c, k, [(18, 25), (25, 25.5), (25, 30.5), (18, 31)])), "#34343c", "#1c1c22", None, s=(1, -1))
    return out


def far_upper(o, J):
    c = o["coat_sh"]
    return cel(capsule(J["far_shoulder"], J["far_elbow"], 12.0, 10.0), c, c)


def far_lower(o, J):
    c = o["coat_sh"]
    el, wr = J["far_elbow"], J["far_wrist"]
    out = cel(capsule(el, lerp(el, wr, 0.8), 10.0, 9.0), c, c)
    out += K.hand_fist((wr[0], wr[1]), K.deg_of(el, wr) - 10, o["skin_sh"], o["skin_sh"], None, k=0.95)
    return out


def near_upper(o, J):
    return cel(capsule(J["near_shoulder"], J["near_elbow"], 14.0, 11.5), o["coat"], o["coat_sh"], o["coat_lt"], s=(6, -3))


def near_lower(o, J):
    el, wr = J["near_elbow"], J["near_wrist"]
    out = K.limb(el, wr, 9.5, 7.5, o["skin"], o["skin_sh"], o["skin_lt"])
    out += cel(capsule(el, lerp(el, wr, 0.8), 12.0, 11.0), o["coat"], o["coat_sh"], o["coat_lt"], s=(5, -3))
    out += cel(capsule(lerp(el, wr, 0.72), lerp(el, wr, 0.84), 11.6, 11.2), o["accent"], o["accent_sh"], None, s=(3, -2))
    return out


def keyboard(o, grip):
    """A mechanical keyboard held level in front of him, its keys up: a dark
    case, three rows of keycaps, one red key (the one he hits hardest)."""
    gx, gy = grip
    x0, x1 = gx - 58, gx + 40
    top, bot = gy - 8, gy + 8
    case = smooth([(x0, top, True), (x1, top - 3, True), (x1 + 2, bot - 2, True), (x0 + 2, bot + 2, True)])
    items = []
    for row, y in enumerate((top - 1, top + 4, top + 9)):
        n = 10 - row
        span = (x1 - x0 - 8)
        for i in range(n):
            kx = x0 + 4 + row * 3 + i * span / 10
            color = o["accent"] if (row, i) == (0, 8) else o["key"]
            items.append(path(smooth([(kx, y - 2.5, True), (kx + span / 10 - 1.5, y - 2.8, True), (kx + span / 10 - 1.2, y + 2.2, True),
                                      (kx + 0.3, y + 2.5, True)]), color, o["key_sh"], 0.7))
    out = cel(case, o["case"], o["case_sh"], "#3c3e48", items, s=(3, -2))
    # the strap's end at the case
    out.append(line([(x0 + 4, top), (x0 - 2, top - 10)], o["accent"], 3.0))
    return out


def near_hand(o, J):
    el, wr = J["near_elbow"], J["near_wrist"]
    deg = K.deg_of(el, wr)
    out = keyboard(o, (wr[0] + 2, wr[1] + 6))
    out += K.hand_open((wr[0], wr[1]), deg + 20, o["skin"], o["skin_sh"], o["skin_lt"], k=1.0)
    return out


def shoe(o, an, near):
    return C.shoe(o, an, near)


#: The parts, in the order they are drawn: (group id, label, part, bone, z, opacity channel).
LAYERS = [
    ("far-arm-upper", "Far Arm - Upper", "far_arm_u", "far_arm_u", 10, ""),
    ("far-arm-lower", "Far Arm - Lower", "far_arm_l", "far_arm_l", 11, ""),
    ("far-thigh", "Far Thigh", "far_leg_u", "far_leg_u", 20, ""),
    ("far-shin", "Far Shin", "far_leg_l", "far_leg_l", 21, ""),
    ("far-foot", "Far Foot", "far_foot", "far_foot", 22, ""),
    ("near-thigh", "Near Thigh", "near_leg_u", "near_leg_u", 30, ""),
    ("near-shin", "Near Shin", "near_leg_l", "near_leg_l", 31, ""),
    ("near-foot", "Near Foot", "near_foot", "near_foot", 32, ""),
    ("torso", "Torso and Hoodie", "torso", "torso", 50, ""),
    ("head", "Head", "head", "head", 60, ""),
    ("eye-open", "Eye - Open", "eye_open", "head", 61, "eye_open"),
    ("eye-shut", "Eye - Shut", "eye_shut", "head", 61, "eye_shut"),
    ("mouth-open", "Mouth - Open", "mouth_open", "head", 61, "mouth_open"),
    ("glasses", "Glasses", "glasses", "head", 62, ""),
    ("headset", "Headset", "headset", "head", 63, ""),
    ("near-arm-upper", "Near Arm - Upper", "near_arm_u", "near_arm_u", 80, ""),
    ("near-arm-lower", "Near Arm - Lower", "near_arm_l", "near_arm_l", 81, ""),
    ("near-hand", "Near Hand and Keyboard", "near_hand", "near_hand", 82, ""),
]


def drawn(o) -> Dict[str, list]:
    out = {"far-arm-upper": far_upper(o, J), "far-arm-lower": far_lower(o, J),
           "torso": C.torso(o) + hoodie(o), "head": head(o),
           "eye-open": C.eyes(o, "open"), "eye-shut": C.eyes(o, "shut"), "mouth-open": C.mouth_open(o), "glasses": C.glasses(o),
           "headset": headset(o),
           "near-arm-upper": near_upper(o, J), "near-arm-lower": near_lower(o, J), "near-hand": near_hand(o, J)}
    for side in ("far", "near"):
        out[f"{side}-thigh"] = C.thigh(o, J, side)
        out[f"{side}-shin"] = C.shin(o, J, side)
        out[f"{side}-foot"] = shoe(o, J[f"{side}_ankle"], side == "near")
    return out


def svg_text() -> str:
    o = LOOK
    K.begin(o["ink"], OW)
    parts = drawn(o)
    for group, label, name, bone, z, channel in LAYERS:
        K.part(group, label, name, bone, z, parts[group], channel, default_on=channel == "eye_open")
    return K.document(
        design="hoodie_developer", layer_id="hoodie_developer", label=VIEW,
        comment=["  <!-- the hoodie_developer: side view facing right, the ground at y=500.",
                 "       Drawn by scripts/svg_art/hoodie_developer_art.py; each part turns about its bone's joint. -->"],
        joints=joints(),
    )


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".svg.tmp")
    tmp.write_text(svg_text(), encoding="utf8")
    tmp.replace(OUT)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
