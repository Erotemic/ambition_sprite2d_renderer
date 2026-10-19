#!/usr/bin/env python3
"""How the Dark Lord's SVG was first drawn (reference, not authority).

    uv run python scripts/svg_art/dark_lord_art.py            # his look (A)
    uv run python scripts/svg_art/dark_lord_art.py --all DIR  # every look, to DIR

Writes ``data/characters/dark_lord/dark_lord.svg``; the SVG owns the art after
this has run once. ``joints(look)`` says where each part turns and
``layers(look)`` lists the parts; ``scripts/build_dark_lord_rig.py`` reads both
and authors the rows.

Jon, 2026-10-18, of three redraws: "A for dark lord", and "keep the other dark
lord variants around, they are good. Might be useful as skins." A is
``iron_tyrant`` (today's kit redrawn: a spiked crown helm with a red visor
slit, plate, a long black cape lined in crimson, a short red tabard, clawed
gauntlets, a rune halberd held two-handed), his look. B (``sorcerer_king``:
lean, ram horns, a long violet robe, a crescent glaive) and C (``warlord``:
hulking, bull horns, a fur mantle, a greataxe leaning head-down) are KEPT,
NOT CAST: this script draws them (``--all``) on the same parts and bones, so
either can become a skin, and nothing registers them.

A man in plate: the breastplate carries one keel ridge, never pecs.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _cel_profile_kit as K  # noqa: E402
from _cel_profile_kit import capsule, ellipse, line, path, smooth  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "ambition_sprite2d_renderer" / "data" / "characters" / "dark_lord" / "dark_lord.svg"
VIEW = "Dark Lord - Side Right"
LOOK = "iron_tyrant"
OW = 1.5
#: The ground under his soles, in SVG units.
GROUND_Y = 500.0

LOOKS = {
    "iron_tyrant": dict(
        label="A: Iron Tyrant - today's kit, redrawn: spiked crown helm, halberd two-handed",
        ink="#120d10", plate="#5c616c", plate_sh="#3b3f48", plate_lt="#8d939e", plate_dk="#24262c",
        trim="#2a2c33", trim_sh="#1a1b20", trim_lt="#43464f",
        cape="#1c1a20", cape_sh="#0f0e12", cape_lt="#2f2c35", lining="#8e1f26", lining_sh="#5f141a",
        cloth="#8e1f26", cloth_sh="#5f141a", cloth_lt="#b5343a",
        glow="#ff3b2f", glow_hi="#ffc2a0", glow_halo="#ff3b2f",
        shaft="#2b2423", shaft_lt="#4a3e3b", blade="#aab0b9", blade_sh="#767d88", blade_lt="#e3e7ec",
        helm="crown", weapon="halberd", cape_kind="long", grip="two", tabard="short",
        pauldron=1.0, limb=1.0, torso_w=1.0, spikes=True),
    "sorcerer_king": dict(
        label="B: Sorcerer-King - lean, ram horns, long violet robe, crescent glaive",
        ink="#140c1a", plate="#3a3546", plate_sh="#26222f", plate_lt="#5d566d", plate_dk="#18151e",
        trim="#c9a043", trim_sh="#8f6d26", trim_lt="#f0d27a",
        cape="#2a1838", cape_sh="#180d22", cape_lt="#3f2752", lining="#5e2c7a", lining_sh="#3e1b52",
        cloth="#4a2462", cloth_sh="#2f163f", cloth_lt="#6a3888",
        glow="#c45cff", glow_hi="#f4d8ff", glow_halo="#b04cff",
        shaft="#1f1a24", shaft_lt="#3a3244", blade="#c6c9d6", blade_sh="#8a8ea0", blade_lt="#f1f2f8",
        horn="#d9cdb4", horn_sh="#a89a7d", horn_lt="#f3ecdc",
        helm="horns", weapon="glaive", cape_kind="long", grip="one", tabard="robe",
        pauldron=0.85, limb=0.86, torso_w=0.9, spikes=False),
    "warlord": dict(
        label="C: Ember Warlord - hulking, bull-horned, fur mantle, greataxe leaning head-down",
        ink="#140c08", plate="#3a3330", plate_sh="#25201e", plate_lt="#5b514c", plate_dk="#171312",
        trim="#9c6b32", trim_sh="#6a4520", trim_lt="#c8924f",
        cape="#3b1e17", cape_sh="#25110c", cape_lt="#55302a", lining="#5a2a1c", lining_sh="#3b190f",
        cloth="#5a3b26", cloth_sh="#3d2617", cloth_lt="#7a563b",
        glow="#ff7a1a", glow_hi="#ffe0a0", glow_halo="#ff6a10",
        shaft="#2e2018", shaft_lt="#4d372a", blade="#8e8a86", blade_sh="#5f5b58", blade_lt="#cfcac4",
        horn="#e6dcc8", horn_sh="#b0a28a", horn_lt="#fbf6ea",
        fur="#4a3a30", fur_lt="#6e5a4a",
        helm="bull", weapon="greataxe", cape_kind="mantle", grip="shoulder", tabard="apron",
        pauldron=1.04, limb=1.18, torso_w=1.22, spikes=True),
}

BASE_J = dict(
    head=(300.0, 140.0), neck=(290.0, 172.0), pelvis=(276.0, 322.0), cape=(272.0, 178.0),
    near_shoulder=(292.0, 200.0), near_elbow=(298.0, 256.0), near_wrist=(356.0, 262.0),
    far_shoulder=(268.0, 196.0), far_elbow=(300.0, 262.0), far_wrist=(360.0, 326.0),
    near_hip=(284.0, 336.0), near_knee=(306.0, 412.0), near_ankle=(304.0, 482.0),
    far_hip=(264.0, 334.0), far_knee=(250.0, 412.0), far_ankle=(234.0, 482.0),
)


def J_of(o) -> Dict[str, Tuple[float, float]]:
    """The drawing's joints for a look."""
    J = dict(BASE_J)
    if o["helm"] == "bull":
        # hulking: head sunk between big shoulders, shoulders forward, wide stance
        J.update(head=(304.0, 150.0), neck=(292.0, 180.0), near_shoulder=(296.0, 206.0), far_shoulder=(270.0, 200.0),
                 near_elbow=(312.0, 262.0), near_wrist=(352.0, 294.0), far_elbow=(262.0, 262.0), far_wrist=(266.0, 318.0),
                 near_knee=(316.0, 412.0), near_ankle=(318.0, 482.0), far_knee=(244.0, 412.0), far_ankle=(222.0, 482.0))
    if o["helm"] == "horns":
        J.update(far_elbow=(240.0, 250.0), far_wrist=(232.0, 300.0))
    # where the near fist closes on the haft: the weapon turns and slides there
    J["grip"] = grip_of(o, J, "near")
    return J


#: Each bone: (parent, the joint of the drawing it turns about). Parents first.
BONES = {
    "body": ("", "pelvis"),
    "pelvis": ("body", "pelvis"),
    "torso": ("body", "pelvis"),
    "cape": ("torso", "cape"),
    "head": ("torso", "neck"),
    "far_pauldron": ("torso", "far_shoulder"),
    "near_pauldron": ("torso", "near_shoulder"),
    "far_arm_u": ("torso", "far_shoulder"),
    "far_arm_l": ("far_arm_u", "far_elbow"),
    "far_hand": ("far_arm_l", "far_wrist"),
    "near_arm_u": ("torso", "near_shoulder"),
    "near_arm_l": ("near_arm_u", "near_elbow"),
    "near_hand": ("near_arm_l", "near_wrist"),
    "weapon": ("near_hand", "grip"),
    "far_leg_u": ("body", "far_hip"),
    "far_leg_l": ("far_leg_u", "far_knee"),
    "far_foot": ("far_leg_l", "far_ankle"),
    "near_leg_u": ("body", "near_hip"),
    "near_leg_l": ("near_leg_u", "near_knee"),
    "near_foot": ("near_leg_l", "near_ankle"),
}


def joints(look: str = LOOK) -> Dict[str, Tuple[float, float]]:
    return J_of(LOOKS[look])


# ------------------------------------------------------------------ shading ---

def cel(sil, base, sh=None, lt=None, extras=(), k=6.0, m=3.0, outline=True, ow=None):
    """A shape with a shade band ``k`` deep down-back and a light band ``m``
    deep up-front, then its ink."""
    return K.cel(sil, base, sh, lt, extras, s=(k, -0.75 * k), l=(m, -0.9 * m), width=ow or 2 * OW, outline=outline)


def pc(o, far=False):
    """The plate colours, darker on the far side."""
    if not far:
        return o["plate"], o["plate_sh"], o["plate_lt"]
    return K.tone(o["plate"], 0.72), K.tone(o["plate_sh"], 0.72), K.tone(o["plate"], 0.9)


def trim_of(o, far=False):
    if not far:
        return o["trim"], o["trim_sh"], o["trim_lt"]
    return K.tone(o["trim"], 0.75), o["trim_sh"], None


lerp = K.lerp


# ------------------------------------------------------------------- pieces ---

def horn(o, root, pts, w0, far=False):
    """A tapered horn from ``root`` along ``pts`` to a point."""
    cl = [root] + pts
    n = len(cl)
    left, right = [], []
    for i, p in enumerate(cl):
        a = cl[max(i - 1, 0)]
        b = cl[min(i + 1, n - 1)]
        ux, uy = K.norm(a, b)
        w = w0 * (1 - i / (n - 1)) ** 0.8
        left.append((p[0] - uy * w, p[1] + ux * w))
        right.append((p[0] + uy * w, p[1] - ux * w))
    sil = smooth(left[:-1] + [cl[-1] + (True,)] + right[-2::-1])
    base = o["horn"] if not far else K.tone(o["horn"], 0.75)
    ridges = [line([lerp(left[i], cl[i], 0.2), lerp(right[i], cl[i], 0.2)], o["horn_sh"], 1.1) for i in range(1, n - 1)]
    return cel(sil, base, o["horn_sh"] if not far else K.tone(o["horn_sh"], 0.75), o["horn_lt"] if not far else None, ridges,
               k=4, m=2, ow=1.8)


def helm(o, J):
    """The helm and its crown or horns; the visor is ``visor``."""
    hx, hy = J["head"]
    out = []
    base, sh, lt = pc(o)
    if o["helm"] == "horns":
        out += horn(o, (hx - 8, hy - 16), [(hx - 30, hy - 30), (hx - 52, hy - 34), (hx - 62, hy - 56), (hx - 54, hy - 76)], 9, far=True)
    if o["helm"] == "bull":
        out += horn(o, (hx - 6, hy - 14), [(hx - 14, hy - 30), (hx - 6, hy - 52), (hx + 12, hy - 64)], 10, far=True)
    sil = smooth([(hx - 22, hy + 16), (hx - 25, hy - 4), (hx - 17, hy - 22), (hx, hy - 29), (hx + 17, hy - 25), (hx + 27, hy - 11),
                  (hx + 31, hy + 4), (hx + 33, hy + 18, True), (hx + 24, hy + 31), (hx + 6, hy + 35), (hx - 14, hy + 33),
                  (hx - 27, hy + 32, True), (hx - 24, hy + 22)])
    seams = [line([(hx + 4, hy - 27), (hx + 2, hy - 4), (hx + 6, hy + 34)], o["plate_dk"], 1.4),
             line([(hx - 20, hy + 22), (hx - 6, hy + 24), (hx + 6, hy + 33)], o["plate_dk"], 1.2)]
    if o["helm"] != "horns":
        for k in range(3):  # breathing holes in the face plate
            seams.append(ellipse(hx + 21 + k * 3.5, hy + 20 + k * 1.2, 1.1, 1.1, o["plate_dk"]))
    out += cel(sil, base, sh, lt, seams, k=7, m=3)
    if o["helm"] == "crown":
        band = smooth([(hx - 24, hy - 8), (hx - 18, hy - 22), (hx + 18, hy - 24), (hx + 30, hy - 10), (hx + 30, hy - 2), (hx + 12, hy - 12),
                       (hx - 16, hy - 10)])
        # the spikes of the crown, leaning back
        for bx, by, tx, ty in ((hx - 20, hy - 16, hx - 40, hy - 62), (hx - 10, hy - 22, hx - 22, hy - 78), (hx + 2, hy - 24, hx - 4, hy - 84),
                               (hx + 14, hy - 22, hx + 14, hy - 72), (hx + 24, hy - 16, hx + 30, hy - 52)):
            s = smooth([(bx - 6, by + 4, True), (tx, ty, True), (bx + 6, by + 2, True)])
            out += cel(s, o["trim"], o["trim_sh"], o["trim_lt"], k=3, m=1.5, ow=1.6)
        out += cel(band, o["trim"], o["trim_sh"], o["trim_lt"], [ellipse(hx + 10, hy - 17, 2.2, 2.2, o["glow"])], k=3, m=1.5, ow=1.6)
    elif o["helm"] == "horns":
        circlet = smooth([(hx - 24, hy - 6), (hx - 16, hy - 20), (hx + 20, hy - 22), (hx + 30, hy - 8), (hx + 31, hy - 2), (hx + 14, hy - 12),
                          (hx - 16, hy - 8)])
        out += cel(circlet, o["trim"], o["trim_sh"], o["trim_lt"], [ellipse(hx + 22, hy - 13, 2.6, 3.0, o["glow"])], k=2.5, m=1.2, ow=1.6)
        fin = smooth([(hx - 18, hy - 20), (hx - 10, hy - 40), (hx + 6, hy - 46, True), (hx + 4, hy - 30), (hx + 14, hy - 24)])
        out += cel(fin, base, sh, lt, k=3, m=1.5, ow=1.6)
        out += horn(o, (hx - 4, hy - 12), [(hx - 26, hy - 24), (hx - 48, hy - 26), (hx - 58, hy - 48), (hx - 50, hy - 70)], 10)
    elif o["helm"] == "bull":
        brow = smooth([(hx - 24, hy - 4), (hx - 18, hy - 22), (hx + 18, hy - 24), (hx + 32, hy - 8), (hx + 34, hy + 2), (hx + 12, hy - 8),
                       (hx - 16, hy - 6)])
        out += cel(brow, o["trim"], o["trim_sh"], o["trim_lt"], k=3, m=1.5, ow=1.6)
        out += horn(o, (hx - 2, hy - 12), [(hx - 18, hy - 30), (hx - 10, hy - 56), (hx + 14, hy - 70)], 11)
    return out


def visor(o, J, lit=True):
    """The visor: a glowing slit (A, C) or eye points in a T (B); unlit, dead."""
    hx, hy = J["head"]
    if o["helm"] == "horns":
        out = [path(smooth([(hx + 12, hy - 4, True), (hx + 31, hy - 6, True), (hx + 32, hy + 2, True), (hx + 24, hy + 2), (hx + 22, hy + 22, True),
                            (hx + 16, hy + 22, True), (hx + 16, hy + 2), (hx + 12, hy + 2, True)]), o["plate_dk"])]
        if lit:
            out += [K.glow(hx + 26, hy - 1, 8, 5, o["glow_halo"], 0.3), ellipse(hx + 26, hy - 1, 3.2, 2.2, o["glow"]),
                    ellipse(hx + 26.5, hy - 1.4, 1.4, 1.0, o["glow_hi"])]
        return out
    slit = smooth([(hx + 10, hy + 1, True), (hx + 32, hy - 2, True), (hx + 33, hy + 5, True), (hx + 12, hy + 7, True)])
    if not lit:
        return [path(slit, o["plate_dk"], o["ink"], 1.2)]
    return [K.glow(hx + 24, hy + 2, 15, 7, o["glow_halo"], 0.28, rot_deg=-6), path(slit, o["glow"], o["ink"], 1.2),
            line([(hx + 15, hy + 3.4), (hx + 30, hy + 1.6)], o["glow_hi"], 1.6)]


def gorget(o, J):
    nx, ny = J["neck"]
    sil = smooth([(nx - 20, ny - 4), (nx - 4, ny - 10), (nx + 14, ny - 8), (nx + 20, ny + 4), (nx + 8, ny + 14), (nx - 16, ny + 12)])
    return cel(sil, o["trim"], o["trim_sh"], o["trim_lt"], [line([(nx - 18, ny + 3), (nx + 18, ny)], o["trim_sh"], 1.2)], k=3, m=1.5)


def _sx(o, J):
    nx = J["neck"][0]
    tw = o["torso_w"]
    return lambda x: nx - 2 + (x - (nx - 2)) * tw


def torso(o, J):
    """The cuirass: one keel ridge, lames over the belly, no pecs."""
    nx, ny = J["neck"]
    px, py = J["pelvis"]
    sx = _sx(o, J)
    pts = [(sx(nx + 12), ny + 2), (sx(nx + 30), ny + 30), (sx(nx + 36), ny + 66), (sx(nx + 26), ny + 106), (sx(px + 24), py - 12),
           (sx(px + 22), py + 6, True), (sx(px - 26), py + 6, True), (sx(px - 28), py - 30), (sx(nx - 38), ny + 70), (sx(nx - 34), ny + 30),
           (sx(nx - 20), ny + 4)]
    base, sh, lt = pc(o)
    det = [line([(sx(nx + 16), ny + 8), (sx(nx + 31), ny + 44), (sx(nx + 30), ny + 80)], o["plate_lt"], 1.6),
           line([(sx(nx - 30), ny + 92), (sx(nx + 6), ny + 100), (sx(nx + 30), ny + 92)], o["plate_dk"], 1.4),
           line([(sx(px - 26), py - 22), (sx(px), py - 18), (sx(px + 24), py - 24)], o["plate_dk"], 1.3),
           line([(sx(nx - 24), ny + 12), (sx(nx - 30), ny + 60), (sx(px - 22), py - 30)], o["plate_dk"], 1.2)]
    if o["helm"] == "crown":
        cx, cy = sx(nx + 27), ny + 40  # the rune boss on the chest
        det += [ellipse(cx, cy, 8, 10, o["trim"], o["ink"], 1.2), ellipse(cx + 1, cy, 5, 7, o["glow"]),
                line([(cx + 1, cy - 6), (cx + 1, cy + 6)], o["glow_hi"], 1.0), line([(cx - 3, cy), (cx + 5, cy)], o["glow_hi"], 1.0)]
    if o["helm"] == "bull":
        # ember cracks: the forge-heat showing through the cuirass
        for crack in ([(sx(nx + 12), ny + 74), (sx(nx + 2), ny + 86), (sx(nx + 8), ny + 98), (sx(nx - 4), ny + 112)],
                      [(sx(nx + 2), ny + 86), (sx(nx - 14), ny + 88)], [(sx(nx - 26), ny + 50), (sx(nx - 18), ny + 64)]):
            det.append(line(crack, o["glow"], 2.6))
            det.append(line(crack, o["glow_hi"], 0.9))
    return cel(smooth(pts), base, sh, lt, det, k=10, m=4)


def hips(o, J):
    """The faulds and the belt (they ride the pelvis)."""
    px, py = J["pelvis"]
    sx = _sx(o, J)
    base, sh, lt = pc(o)
    fauld = smooth([(sx(px - 30), py - 4), (sx(px + 26), py - 6), (sx(px + 34), py + 40), (sx(px + 8), py + 48), (sx(px - 20), py + 46),
                    (sx(px - 38), py + 38)])
    fd = [line([(sx(px - 34), py + 12), (sx(px + 28), py + 10)], o["plate_dk"], 1.3),
          line([(sx(px - 36), py + 26), (sx(px + 31), py + 25)], o["plate_dk"], 1.3)]
    out = cel(fauld, base, sh, lt, fd, k=6, m=3)
    belt = smooth([(sx(px - 30), py - 14, True), (sx(px + 26), py - 18, True), (sx(px + 27), py - 4, True), (sx(px - 29), py, True)])
    bk = [ellipse(sx(px + 20), py - 9, 5, 6, o["trim_lt"], o["ink"], 1.0)]
    if o["helm"] == "crown":
        bk.append(ellipse(sx(px + 20), py - 9, 2.4, 3.2, o["glow"]))
    out += cel(belt, o["trim"], o["trim_sh"], o["trim_lt"], bk, k=3, m=1.5, ow=1.6)
    return out


def tabard(o, J):
    px, py = J["pelvis"]
    kind = o["tabard"]
    if kind == "short":
        sil = smooth([(px + 2, py - 2, True), (px + 32, py - 4, True), (px + 46, py + 50), (px + 56, py + 104), (px + 44, py + 112, True),
                      (px + 30, py + 104), (px + 16, py + 114, True), (px + 4, py + 56)])
        det = [line([(px + 14, py + 4), (px + 32, py + 92)], o["cloth_sh"], 1.2),
               line([(px + 8, py + 60), (px + 18, py + 112)], o["trim_lt"], 1.6),
               line([(px + 42, py + 50), (px + 52, py + 104)], o["trim_lt"], 1.6)]
    elif kind == "apron":
        sil = smooth([(px + 2, py - 2, True), (px + 34, py - 4, True), (px + 44, py + 40), (px + 46, py + 74, True), (px + 30, py + 78),
                      (px + 18, py + 72, True), (px + 8, py + 40)])
        det = [ellipse(px + 30, py + 30, 2, 2, o["trim"]), ellipse(px + 34, py + 50, 2, 2, o["trim"])]
    elif kind == "robe":
        # B: a long robe from the belt to the ankles, split at the front
        sil = smooth([(px - 34, py - 2), (px + 28, py - 4), (px + 44, py + 60), (px + 60, py + 150), (px + 50, py + 164, True), (px + 30, py + 158),
                      (px + 10, py + 166), (px - 14, py + 160), (px - 40, py + 168, True), (px - 54, py + 160), (px - 44, py + 80)])
        det = [line([(px + 2, py + 10), (px + 4, py + 90), (px + 10, py + 160)], o["cloth_sh"], 1.6),
               line([(px - 24, py + 20), (px - 32, py + 100), (px - 34, py + 160)], o["cloth_sh"], 1.4),
               path(smooth([(px - 60, py + 150), (px + 70, py + 140), (px + 70, py + 200), (px - 60, py + 200)]), o["trim"]),
               path(smooth([(px - 60, py + 156), (px + 70, py + 147), (px + 70, py + 200), (px - 60, py + 200)]), o["cloth"]),
               line([(px - 60, py + 148), (px + 70, py + 138)], o["trim_lt"], 1.0)]
        return cel(sil, o["cloth"], o["cloth_sh"], o["cloth_lt"], det, k=8, m=3)
    else:
        return []
    return cel(sil, o["cloth"], o["cloth_sh"], o["cloth_lt"], det, k=5, m=2.5)


def thigh(o, J, side):
    far = side == "far"
    base, sh, lt = pc(o, far)
    lr = o["limb"]
    hip, knee = J[f"{side}_hip"], J[f"{side}_knee"]
    return cel(capsule(lerp(hip, knee, 0.15), knee, 17 * lr, 13 * lr), base, sh, lt,
               [line([lerp(hip, knee, 0.55), lerp(hip, knee, 0.6)], o["plate_dk"], 1.0)], k=6, m=3)


def shin(o, J, side):
    """The greave and the knee cop over the joint."""
    far = side == "far"
    base, sh, lt = pc(o, far)
    lr = o["limb"]
    knee, ankle = J[f"{side}_knee"], J[f"{side}_ankle"]
    out = cel(capsule(knee, ankle, 13 * lr, 9 * lr), base, sh, lt,
              [line([(knee[0] + 9 * lr, knee[1] + 14), (ankle[0] + 7 * lr, ankle[1] - 12)], o["plate_lt"] if not far else lt, 1.4)], k=5, m=2.5)
    kx, ky = knee
    cop = smooth([(kx - 10 * lr, ky - 6), (kx + 2, ky - 14 * lr), (kx + 15 * lr, ky - 4), (kx + 17 * lr, ky + 6, True), (kx + 4, ky + 12 * lr),
                  (kx - 8 * lr, ky + 8)])
    tb, tsh, tlt = trim_of(o, far)
    out += cel(cop, tb, tsh, tlt, [ellipse(kx + 3, ky - 1, 2, 2, o["trim_sh"])], k=3, m=1.5, ow=1.8)
    return out


def sabaton(o, J, side):
    far = side == "far"
    base, sh, lt = pc(o, far)
    s = o["limb"]
    ax, ay = J[f"{side}_ankle"]
    foot = smooth([(ax - 13 * s, ay - 10), (ax + 8 * s, ay - 10), (ax + 22 * s, ay + 1), (ax + 40 * s, ay + 10), (ax + 42 * s, ay + 18, True),
                   (ax - 15 * s, ay + 18, True), (ax - 17 * s, ay + 4)])
    return cel(foot, base, sh, lt, [line([(ax + 6 * s, ay - 8), (ax + 4 * s, ay + 17)], o["plate_dk"], 1.2),
                                    line([(ax + 18 * s, ay - 1), (ax + 16 * s, ay + 17)], o["plate_dk"], 1.2)], k=4, m=2)


def fist(o, H, far=False, claws=True):
    """A gauntlet closed round a vertical shaft at ``H``; knuckles forward."""
    hx, hy = H
    base, sh, lt = pc(o, far)
    out = []
    back = smooth([(hx - 13, hy - 10), (hx - 2, hy - 13), (hx + 4, hy - 4), (hx + 2, hy + 10), (hx - 12, hy + 11), (hx - 16, hy)])
    out += cel(back, base, sh, lt, k=3, m=1.5, ow=1.7)
    for k in range(4):
        y = hy - 9 + k * 6
        a, b = (hx - 2, y), (hx + 11, y + 1)
        out += cel(capsule(a, b, 3.4, 3.0), base, sh, lt, [ellipse(b[0] - 3, b[1], 1.2, 1.2, o["plate_dk"])], k=1.5, m=0.8, ow=1.3)
        if claws:
            out.append(path(smooth([(b[0] + 1, b[1] - 3, True), (b[0] + 8, b[1] + 1, True), (b[0] + 1, b[1] + 3, True)]), o["trim_lt"], o["ink"], 1.0))
    out += cel(capsule((hx - 10, hy - 8), (hx + 4, hy - 15), 3.8, 3.2), base, sh, lt, k=1.5, m=0.8, ow=1.3)
    return out


def claw_hand(o, wr, el, far=False):
    """An open gauntlet hanging from the wrist: four jointed fingers with claws."""
    base, sh, lt = pc(o, far)
    ux, uy = K.norm(el, wr)
    p = K.along(wr, (wr[0] + ux, wr[1] + uy))
    out = []
    for spread, ln in ((-6.5, 18), (-2.2, 21), (2.2, 20), (6.5, 16)):
        a, b = p(12, spread), p(12 + ln * 0.55, spread * 1.25 + 3)
        c = p(12 + ln, spread * 1.3 + 8)
        out += K.group([(capsule(a, b, 3.0, 2.6), base, sh, lt, [], (1.5, -1.1), (0.8, -0.7)),
                        (capsule(b, c, 2.6, 2.0), base, sh, lt, [], (1.5, -1.1), (0.8, -0.7))], 1.3)
        d = K.norm(b, c)
        tip = (c[0] + d[0] * 9, c[1] + d[1] * 9)
        out.append(path(smooth([(c[0] - d[1] * 2.4, c[1] + d[0] * 2.4, True), tip + (True,), (c[0] + d[1] * 2.4, c[1] - d[0] * 2.4, True)]),
                        o["trim_lt"], o["ink"], 1.0))
    palm = smooth([p(-2, -8), p(12, -9), p(16, 0), p(12, 9), p(-2, 8)])
    out += cel(palm, base, sh, lt, k=2, m=1, ow=1.7)
    out += cel(capsule(p(4, 7), p(14, 14), 3.2, 2.6), base, sh, lt, k=1.5, m=0.8, ow=1.3)
    return out


def upper_arm(o, J, side):
    far = side == "far"
    base, sh, lt = pc(o, far)
    lr = o["limb"]
    return cel(capsule(J[f"{side}_shoulder"], J[f"{side}_elbow"], 13 * lr, 11 * lr), base, sh, lt, k=5, m=2.5)


def forearm(o, J, side):
    """The vambrace, the couter over the elbow and the flared cuff."""
    far = side == "far"
    base, sh, lt = pc(o, far)
    lr = o["limb"]
    e, w = J[f"{side}_elbow"], J[f"{side}_wrist"]
    out = cel(capsule(e, lerp(e, w, 0.92), 11 * lr, 12.5 * lr), base, sh, lt,
              [line([lerp(e, w, 0.5), lerp(e, w, 0.8)], o["plate_dk"], 1.1)], k=5, m=2.5)
    ex, ey = e
    tb, tsh, tlt = trim_of(o, far)
    cop = smooth([(ex - 9 * lr, ey - 8 * lr), (ex + 8 * lr, ey - 7 * lr), (ex + 10 * lr, ey + 6 * lr), (ex - 2, ey + 10 * lr),
                  (ex - 16 * lr, ey + 8 * lr, True), (ex - 11 * lr, ey + 2)])
    out += cel(cop, tb, tsh, tlt, k=2.5, m=1.2, ow=1.7)
    cx, cy = lerp(e, w, 0.86)
    fx, fy = K.norm(e, w)
    cuff = smooth([(cx - fy * 14 * lr, cy + fx * 14 * lr), (cx + fx * 12 - fy * 12 * lr, cy + fy * 12 + fx * 12 * lr),
                   (cx + fx * 12 + fy * 12 * lr, cy + fy * 12 - fx * 12 * lr), (cx + fy * 14 * lr, cy - fx * 14 * lr)])
    out += cel(cuff, tb, tsh, tlt, k=2, m=1, ow=1.6)
    return out


def shaft_x(y):
    return 380 - 14 * (498 - y) / 414


def grip_of(o, J, side) -> Tuple[float, float] | None:
    """Where a fist closes on the weapon (None: an open hand)."""
    if side == "near":
        return (354.0, 296.0) if o["grip"] == "shoulder" else (shaft_x(266) - 4, 266.0)
    return (shaft_x(330) - 4, 330.0) if o["grip"] == "two" else None


def hand(o, J, side):
    far = side == "far"
    H = grip_of(o, J, side)
    if H is None:
        return claw_hand(o, J[f"{side}_wrist"], J[f"{side}_elbow"], far)
    return fist(o, H, far)


def sleeve(o, J):
    """B: a wide hanging sleeve on the near upper arm."""
    if o["tabard"] != "robe":
        return []
    s, e = J["near_shoulder"], J["near_elbow"]
    sil = smooth([(s[0] - 14, s[1] - 2), (s[0] + 14, s[1] + 4), (e[0] + 16, e[1] - 2), (e[0] + 18, e[1] + 30), (e[0] + 6, e[1] + 46, True),
                  (e[0] - 6, e[1] + 30), (e[0] - 18, e[1] + 40, True), (e[0] - 20, e[1] + 10)])
    det = [path(smooth([(e[0] - 20, e[1] + 30), (e[0] + 20, e[1] + 22), (e[0] + 20, e[1] + 60), (e[0] - 20, e[1] + 60)]), o["trim"]),
           path(smooth([(e[0] - 20, e[1] + 35), (e[0] + 20, e[1] + 27), (e[0] + 20, e[1] + 60), (e[0] - 20, e[1] + 60)]), o["cloth"]),
           line([(e[0] - 2, e[1] - 2), (e[0] + 4, e[1] + 36)], o["cloth_sh"], 1.4)]
    return cel(sil, o["cloth"], o["cloth_sh"], o["cloth_lt"], det, k=6, m=2.5)


def pauldron(o, J, side):
    far = side == "far"
    sx, sy = J[f"{side}_shoulder"]
    k = o["pauldron"] * (0.92 if far else 1.0)
    base, sh, lt = pc(o, far)
    P = lambda dx, dy: (sx + dx * k, sy - 7 + dy * k)  # noqa: E731
    out = []
    if o["spikes"]:
        tips = [(-44, -38), (-26, -50), (-8, -48)] if o["helm"] != "bull" else [(-42, -30), (-24, -44), (-4, -42), (14, -30)]
        bases = [(-20, -12), (-8, -20), (6, -22), (18, -16)]
        tb = o["trim"] if not far else K.tone(o["trim"], 0.7)
        for i, t in enumerate(tips):
            b = bases[i]
            s = smooth([P(b[0] - 7, b[1] + 4) + (True,), P(*t) + (True,), P(b[0] + 7, b[1] + 2) + (True,)])
            out += cel(s, tb, o["trim_sh"], o["trim_lt"] if not far else None, k=3, m=1.5, ow=1.6)
    for j in (2, 1):
        y0 = 12 + j * 10
        out += cel(smooth([P(-22, y0 - 6), P(26, y0 - 8), P(30, y0 + 6), P(4, y0 + 12), P(-20, y0 + 8)]), base, sh, lt, k=3, m=1.5, ow=1.8)
    dome = smooth([P(-28, 8), P(-24, -14), P(-4, -26), P(18, -21), P(31, -3), P(29, 14), P(6, 21), P(-18, 19)])
    det = [line([P(-22, 10), P(4, 16), P(28, 10)], o["trim_lt"] if not far else o["trim"], 2.0)]
    if o["helm"] == "horns":
        det = [path(smooth([P(-30, 6), P(30, 4), P(30, 30), P(-30, 30)]), o["trim"]), line([P(-26, 6), P(28, 3)], o["trim_lt"], 1.2)]
    out += cel(dome, base, sh, lt, det, k=7, m=3)
    return out


def cape(o, J):
    nx, ny = J["neck"]
    if o["cape_kind"] == "long":
        flare = 1.0 if o["helm"] == "crown" else 1.18
        hem = []
        x0, x1 = nx - 30, nx - 30 - 92 * flare
        n = 7
        for i in range(n + 1):
            t = i / n
            x = x0 + (x1 - x0) * t
            y = 494 - (10 if i % 2 else 0) + (4 if o["helm"] == "horns" else 0) * (i % 2 == 0)
            hem.append((x, y, True))
        outer = [(nx - 14, ny + 2), (nx - 36, ny + 16), (nx - 58, ny + 80), (nx - 30 - 76 * flare, ny + 190), (nx - 30 - 92 * flare, 494, True)]
        sil = smooth(outer + hem[::-1][1:] + [(nx - 36, 420), (nx - 30, 330), (nx - 20, 240)])
        lining_sil = smooth([(p[0] + 10, p[1]) + tuple(p[2:]) for p in outer] + [(p[0] + 10, p[1] - 2, True) for p in hem[::-1][1:]] +
                            [(nx - 18, 420), (nx - 14, 330), (nx - 8, 240)])
        folds = [line([(nx - 40, ny + 40), (nx - 70, ny + 200), (nx - 84, 488)], o["cape_sh"], 2.0),
                 line([(nx - 30, ny + 60), (nx - 46, ny + 220), (nx - 54, 480)], o["cape_sh"], 1.6)]
        if o["helm"] == "horns":
            folds.append(line([(nx - 30, ny + 2), (nx - 30, 300), (nx - 36, 420), (nx - 32, 492)], o["trim"], 2.2))
        out = cel(lining_sil, o["lining"], o["lining_sh"], None, k=6, m=2)
        out += cel(sil, o["cape"], o["cape_sh"], o["cape_lt"], folds, k=14, m=4)
        return out
    # C: a short ragged mantle to the hip
    outer = [(nx - 10, ny), (nx - 40, ny + 14), (nx - 66, ny + 70), (nx - 78, ny + 130, True)]
    hem = [(nx - 64, ny + 118, True), (nx - 58, ny + 146, True), (nx - 46, ny + 126, True), (nx - 36, ny + 156, True), (nx - 26, ny + 130, True),
           (nx - 18, ny + 150, True)]
    sil = smooth(outer + hem + [(nx - 16, ny + 80), (nx - 8, ny + 30)])
    lining = smooth([(p[0] + 8, p[1] + 2) + tuple(p[2:]) for p in outer + hem] + [(nx - 6, ny + 80), (nx, ny + 30)])
    out = cel(lining, o["lining"], o["lining_sh"], None, k=5, m=2)
    out += cel(sil, o["cape"], o["cape_sh"], o["cape_lt"], [line([(nx - 40, ny + 30), (nx - 54, ny + 120)], o["cape_sh"], 1.8)], k=10, m=3)
    return out


def fur_collar(o, J):
    if o["helm"] != "bull":
        return []
    nx, ny = J["neck"]
    K.svg.INK = o["ink"]
    edge = [(nx - 52, ny + 26), (nx - 40, ny + 4), (nx - 16, ny - 8), (nx + 8, ny - 6), (nx + 24, ny + 6)]
    out = K.svg.fringe(edge, 9, 14, -0.2, o["fur"], tip=o["fur_lt"], ow=1.4, inset=10, flip=False, jitter=0.3)
    body = smooth([(nx - 54, ny + 28), (nx - 40, ny + 2), (nx - 16, ny - 10), (nx + 10, ny - 8), (nx + 26, ny + 6), (nx + 14, ny + 18),
                   (nx - 20, ny + 18), (nx - 44, ny + 36)])
    out += cel(body, o["fur"], K.tone(o["fur"], 0.7), o["fur_lt"], [line([(nx - 30, ny + 10), (nx - 22, ny + 4)], o["fur_lt"], 1.2),
                                                                   line([(nx - 6, ny + 6), (nx + 2, ny)], o["fur_lt"], 1.2)], k=4, m=2)
    return out


def weapon(o, J):
    kind = o["weapon"]
    ink = o["ink"]
    out = []
    if kind in ("halberd", "glaive"):
        bot, top = (380.0, 498.0), (366.0, 84.0)
        out.append(path(capsule(bot, top, 4.4, 4.4), o["shaft"], ink, 1.8))
        out.append(line([lerp(bot, top, 0.05), lerp(bot, top, 0.95)], o["shaft_lt"], 1.2))
        for t in (0.42, 0.62):
            a = lerp(bot, top, t)
            out += cel(smooth([(a[0] - 6, a[1] - 3, True), (a[0] + 6, a[1] - 3, True), (a[0] + 6, a[1] + 3, True), (a[0] - 6, a[1] + 3, True)]),
                       o["trim"], o["trim_sh"], o["trim_lt"], k=1.5, m=0.8, ow=1.2)
        tx, ty = top
        if kind == "halberd":
            spike_ = smooth([(tx - 5, ty + 6, True), (tx - 1, ty - 44, True), (tx + 5, ty + 6, True)])
            out += cel(spike_, o["blade"], o["blade_sh"], o["blade_lt"], k=2, m=1, ow=1.6)
            axe = smooth([(tx + 2, ty + 10, True), (tx + 22, ty + 2), (tx + 40, ty - 8, True), (tx + 36, ty + 22), (tx + 40, ty + 52, True),
                          (tx + 22, ty + 44), (tx + 3, ty + 40, True)])
            out += cel(axe, o["blade"], o["blade_sh"], o["blade_lt"],
                       [line([(tx + 30, ty - 2), (tx + 34, ty + 22), (tx + 32, ty + 44)], o["blade_lt"], 2.0),
                        line([(tx + 12, ty + 16), (tx + 20, ty + 26), (tx + 14, ty + 34)], o["glow"], 1.6)], k=5, m=2, ow=1.8)
            hook = smooth([(tx - 2, ty + 16, True), (tx - 20, ty + 22), (tx - 30, ty + 36, True), (tx - 16, ty + 30), (tx - 2, ty + 32, True)])
            out += cel(hook, o["blade"], o["blade_sh"], o["blade_lt"], k=3, m=1.5, ow=1.6)
            out.append(ellipse(tx + 1, ty + 26, 5.5, 6.5, o["trim"], ink, 1.3))
            out.append(ellipse(tx + 1, ty + 26, 3, 4, o["glow"]))
        else:
            # a crescent glaive: a long curved blade sweeping forward and up
            blade = smooth([(tx - 4, ty + 22, True), (tx + 8, ty - 6), (tx + 30, ty - 30), (tx + 58, ty - 42, True), (tx + 40, ty - 22),
                            (tx + 22, ty + 2), (tx + 6, ty + 34, True)])
            out += cel(blade, o["blade"], o["blade_sh"], o["blade_lt"], [line([(tx + 10, ty + 2), (tx + 32, ty - 24)], o["glow"], 1.6)], k=5, m=2,
                       ow=1.8)
            fin = smooth([(tx - 3, ty + 14, True), (tx - 22, ty + 4, True), (tx - 14, ty + 24), (tx - 3, ty + 30, True)])
            out += cel(fin, o["trim"], o["trim_sh"], o["trim_lt"], k=2, m=1, ow=1.4)
            out.append(K.glow(tx + 1, ty + 40, 11, 11, o["glow_halo"], 0.3))
            out.append(ellipse(tx + 1, ty + 40, 6, 7, o["trim"], ink, 1.3))
            out.append(ellipse(tx + 1, ty + 40, 3.6, 4.6, o["glow"]))
            out.append(ellipse(tx + 2, ty + 38, 1.4, 1.6, o["glow_hi"]))
        b2 = smooth([(bot[0] - 5, bot[1] - 14, True), (bot[0] + 5, bot[1] - 14, True), (bot[0] + 1, bot[1] + 2, True)])
        out += cel(b2, o["trim"], o["trim_sh"], o["trim_lt"], k=1.5, m=0.8, ow=1.4)
        return out
    # C: a greataxe leaning head-down on the ground in front, haft up to the hand
    S = (414.0, 440.0)
    a, b = (338.0, 262.0), (S[0] + 10, S[1] + 26)
    out.append(path(capsule(a, b, 5.8, 5.8), o["shaft"], ink, 1.8))
    out.append(line([lerp(a, b, 0.04), lerp(a, b, 0.8)], o["shaft_lt"], 1.4))
    for t in (0.18, 0.62):
        q = lerp(a, b, t)
        out.append(ellipse(q[0], q[1], 7, 7, o["trim"], ink, 1.2))
    sx, sy = S
    blade = smooth([(sx - 2, sy - 16, True), (sx + 22, sy - 30), (sx + 58, sy - 46, True), (sx + 66, sy + 8), (sx + 56, sy + 60, True),
                    (sx + 26, sy + 42), (sx + 4, sy + 18, True)])
    out += cel(blade, o["blade"], o["blade_sh"], o["blade_lt"],
               [line([(sx + 56, sy - 36), (sx + 63, sy + 10), (sx + 54, sy + 52)], o["blade_lt"], 2.8),
                line([(sx + 14, sy - 6), (sx + 26, sy + 6), (sx + 18, sy + 20)], o["glow"], 2.0)], k=7, m=2.5, ow=2.0)
    back = smooth([(sx - 2, sy - 8, True), (sx - 34, sy + 10, True), (sx - 4, sy + 10, True)])
    out += cel(back, o["blade"], o["blade_sh"], o["blade_lt"], k=3, m=1.2, ow=1.6)
    out += cel(capsule((sx - 4, sy - 16), (sx + 8, sy + 20), 7, 7), o["trim"], o["trim_sh"], o["trim_lt"], k=2, m=1, ow=1.6)
    return out


# ------------------------------------------------------------------- effects ---

def cast_fx(o, J):
    """A rune bolt kindled in the free hand (``fx_cast``): a ring of runes
    round a burning core, in front of the far fist."""
    wx, wy = J["far_wrist"]
    cx, cy = wx + 34, wy + 2
    out = [K.glow(cx, cy, 30, 30, o["glow_halo"], 0.22), ellipse(cx, cy, 22, 22, "none", o["ink"], 5.0),
           ellipse(cx, cy, 22, 22, "none", o["glow"], 2.6)]
    for k in range(6):
        a = k * 60
        p = K.xf((cx, cy), a, [(14, -3, True), (19, 0, True), (14, 3, True)])
        out.append(path(smooth(p), o["glow_hi"], o["ink"], 0.8))
    out += [ellipse(cx, cy, 10, 10, o["glow"], o["ink"], 1.4), ellipse(cx - 2, cy - 2, 4.5, 4.5, o["glow_hi"])]
    return out


def summon_fx(o, J):
    """Spikes of black iron out of the ground ahead of him, a rune ring at
    their roots (``fx_summon``)."""
    px = J["pelvis"][0]
    out = [K.glow(px + 190, GROUND_Y - 2, 120, 12, o["glow_halo"], 0.3),
           path(smooth([(px + 80, GROUND_Y - 2), (px + 190, GROUND_Y - 12), (px + 300, GROUND_Y - 2), (px + 190, GROUND_Y + 6)]), "none",
                o["glow"], 2.0)]
    for x, h, lean in ((px + 110, 70, -6), (px + 150, 112, 4), (px + 196, 140, -2), (px + 242, 100, 8), (px + 280, 60, 3)):
        sil = smooth([(x - 13, GROUND_Y + 2, True), (x + lean - 2, GROUND_Y - h + 10), (x + lean, GROUND_Y - h, True),
                      (x + lean + 3, GROUND_Y - h + 12), (x + 13, GROUND_Y + 2, True)])
        out += cel(sil, o["plate_dk"], "#000000", o["plate_sh"], [line([(x + lean * 0.4, GROUND_Y - h * 0.8), (x - 4, GROUND_Y)], o["glow"], 1.8)],
                   k=4, m=2, ow=1.8)
    return out


def slash_fx(o, J):
    """The blade's trail (``fx_slash``, on the weapon's bone): a crescent about
    the grip that starts AT the blade and thins back along the way it came
    (the swing turns the weapon clockwise, so behind the blade is to its
    left); nothing ahead of the blade, and the tail tapers to nothing."""
    import math
    gx, gy = grip_of(o, J, "near")
    gx += 4
    out = []
    pts_o, pts_i = [], []
    n = 16
    for i in range(n + 1):
        t = i / n  # 0 at the blade, 1 at the tail
        a = math.radians(-84 - 84 * t)
        r_o = 214 - 10 * t
        r_i = r_o - 52 * (1 - t) ** 1.3 - 2
        pts_o.append((gx + math.cos(a) * r_o, gy + math.sin(a) * r_o))
        pts_i.append((gx + math.cos(a) * r_i, gy + math.sin(a) * r_i))
    sil = smooth([pts_o[0] + (True,)] + pts_o[1:-1] + [pts_o[-1] + (True,)] + pts_i[-2:0:-1] + [pts_i[0] + (True,)])
    out.append(path(sil, o["glow"], extra=' fill-opacity="0.5"'))
    core = [((p[0] + q[0]) / 2, (p[1] + q[1]) / 2) for p, q in zip(pts_o[:11], pts_i[:11])]
    out.append(line(core, o["glow_hi"], 2.6))
    return out


# --------------------------------------------------------------------- parts ---

def layers(look: str = LOOK) -> List[Tuple[str, str, str, str, float, str]]:
    """The parts, in the order they are drawn: (group id, label, part, bone, z, opacity channel)."""
    o = LOOKS[look]
    front = o["grip"] == "two"  # a far arm gripping the shaft crosses in front of his chest
    fz = 56 if front else 6
    return [
        ("cape", "Cape", "cape", "cape", 5, ""),
        ("far-arm-upper", "Far Arm - Upper", "far_arm_u", "far_arm_u", fz, ""),
        ("far-arm-lower", "Far Arm - Lower", "far_arm_l", "far_arm_l", fz + 1, ""),
        ("far-hand", "Far Hand", "far_hand", "far_hand", fz + 2, ""),
        ("far-pauldron", "Far Pauldron", "far_pauldron", "far_pauldron", 9, ""),
        ("far-thigh", "Far Thigh", "far_leg_u", "far_leg_u", 20, ""),
        ("far-foot", "Far Foot", "far_foot", "far_foot", 21, ""),
        ("far-shin", "Far Shin", "far_leg_l", "far_leg_l", 22, ""),
        ("near-thigh", "Near Thigh", "near_leg_u", "near_leg_u", 30, ""),
        ("near-foot", "Near Foot", "near_foot", "near_foot", 31, ""),
        ("near-shin", "Near Shin", "near_leg_l", "near_leg_l", 32, ""),
        ("tabard", "Tabard", "tabard", "pelvis", 34, ""),
        ("torso", "Cuirass", "torso", "torso", 38, ""),
        ("hips", "Faulds and Belt", "hips", "pelvis", 40, ""),
        ("gorget", "Gorget", "gorget", "torso", 44, ""),
        ("fur", "Fur Collar", "fur", "torso", 46, ""),
        ("head", "Helm", "head", "head", 50, ""),
        ("eye-open", "Visor - Lit", "eye_open", "head", 51, "eye_open"),
        ("eye-dead", "Visor - Dark", "eye_dead", "head", 51, "eye_dead"),
        ("fx-slash", "FX - Slash", "fx_slash", "weapon", 54, "fx_slash"),
        ("weapon", "Weapon", "weapon", "weapon", 55, ""),
        ("near-arm-upper", "Near Arm - Upper", "near_arm_u", "near_arm_u", 60, ""),
        ("near-sleeve", "Near Sleeve", "near_sleeve", "near_arm_u", 60.5, ""),
        ("near-arm-lower", "Near Arm - Lower", "near_arm_l", "near_arm_l", 61, ""),
        ("near-hand", "Near Hand", "near_hand", "near_hand", 62, ""),
        ("near-pauldron", "Near Pauldron", "near_pauldron", "near_pauldron", 65, ""),
        ("fx-cast", "FX - Cast", "fx_cast", "far_hand", 70, "fx_cast"),
        ("fx-summon", "FX - Summon", "fx_summon", "body", 70, "fx_summon"),
    ]


def drawn(o, J) -> Dict[str, list]:
    out = {"cape": cape(o, J), "tabard": tabard(o, J), "torso": torso(o, J), "hips": hips(o, J), "gorget": gorget(o, J),
           "fur": fur_collar(o, J), "head": helm(o, J), "eye-open": visor(o, J, True), "eye-dead": visor(o, J, False),
           "weapon": weapon(o, J), "near-sleeve": sleeve(o, J), "fx-slash": slash_fx(o, J), "fx-cast": cast_fx(o, J),
           "fx-summon": summon_fx(o, J)}
    for side in ("far", "near"):
        out[f"{side}-arm-upper"] = upper_arm(o, J, side)
        out[f"{side}-arm-lower"] = forearm(o, J, side)
        out[f"{side}-hand"] = hand(o, J, side)
        out[f"{side}-pauldron"] = pauldron(o, J, side)
        out[f"{side}-thigh"] = thigh(o, J, side)
        out[f"{side}-shin"] = shin(o, J, side)
        out[f"{side}-foot"] = sabaton(o, J, side)
    return out


def svg_text(look: str = LOOK) -> str:
    o = LOOKS[look]
    J = J_of(o)
    K.begin(o["ink"], OW)
    parts = drawn(o, J)
    for group, label, name, bone, z, channel in layers(look):
        K.part(group, label, name, bone, z, parts[group], channel, default_on=channel == "eye_open")
    note = ("the Dark Lord's look (Jon chose A, 2026-10-18)" if look == LOOK
            else "KEPT, NOT CAST: a Dark Lord look Jon kept as a possible skin (2026-10-18), not registered in the cast")
    return K.document(
        design=f"dark-lord-{look}", layer_id="dark-lord", label=VIEW,
        comment=[f"  <!-- {note}: side view facing right, the ground at y=500.",
                 "       Drawn by scripts/svg_art/dark_lord_art.py; each part turns about its bone's joint. -->"],
        joints=J,
    )


def main() -> None:
    if len(sys.argv) > 2 and sys.argv[1] == "--all":
        out = Path(sys.argv[2])
        out.mkdir(parents=True, exist_ok=True)
        for look in LOOKS:
            (out / f"dark_lord_{look}.svg").write_text(svg_text(look), encoding="utf8")
            print(out / f"dark_lord_{look}.svg")
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".svg.tmp")
    tmp.write_text(svg_text(), encoding="utf8")
    tmp.replace(OUT)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
