#!/usr/bin/env python3
"""How the Weird Hermit's SVG was first drawn (reference, not authority).

    uv run python scripts/svg_art/weird_hermit_art.py            # his look (B)
    uv run python scripts/svg_art/weird_hermit_art.py --all DIR  # every look, to DIR

Writes ``data/characters/weird_hermit/weird_hermit.svg``; the SVG owns the art
after this has run once. ``JOINTS`` says where each part turns and ``LAYERS``
lists the parts; ``scripts/build_weird_hermit_rig.py`` reads both and authors
the rows.

Jon, 2026-10-18, of three redraws of the hermit he had called old bad art:
"All 3 hermits are good. I like B as the default. Keep the others too." B is
``sunbaked`` (a red rag, wiry grey hair and moustache, patched green shorts),
his look. A (``faithful``, the old hermit redrawn) and C (``cave``, a pale
cave hermit with a long white moustache) are KEPT, NOT CAST: this script
draws them (``--all``) and nothing registers them.

The read of the old design is kept: a hunch, a head rag knotted behind, an
absurdly long drooping nose, a moustache, a bare wrinkled torso with ribs and
a pot belly (never a chest that reads as breasts), baggy shorts on a rope
belt, knobby knees, bare long feet, and unsettlingly long fingers.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Dict, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import svgkit as svg  # noqa: E402
from svgkit import capsule, clipped, ellipse, line, part, path, smooth  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "ambition_sprite2d_renderer" / "data" / "characters" / "weird_hermit" / "weird_hermit.svg"
VIEW = "Weird Hermit - Side Right"
LOOK = "sunbaked"
W, H = 560, 560
INK = "#1d1714"
OW = 1.7

#: The ground under his soles, in SVG units.
GROUND_Y = 470.0
#: Where each bone turns (SVG units): ``bone: (parent, x, y)``, parents first.
JOINTS: Dict[str, Tuple[str, float, float]] = {
    "body": ("", 252.0, 356.0),
    "torso": ("body", 252.0, 356.0),
    "head": ("torso", 304.0, 250.0),
    "near_arm_u": ("torso", 290.0, 268.0),
    "near_arm_l": ("near_arm_u", 300.0, 318.0),
    "near_hand": ("near_arm_l", 324.0, 344.0),
    "far_arm_u": ("torso", 268.0, 264.0),
    "far_arm_l": ("far_arm_u", 258.0, 316.0),
    "far_hand": ("far_arm_l", 274.0, 346.0),
    "near_leg_u": ("body", 260.0, 362.0),
    "near_leg_l": ("near_leg_u", 284.0, 408.0),
    "near_foot": ("near_leg_l", 270.0, 452.0),
    "far_leg_u": ("body", 240.0, 360.0),
    "far_leg_l": ("far_leg_u", 256.0, 410.0),
    "far_foot": ("far_leg_l", 236.0, 452.0),
}


def P(name):
    return JOINTS[name][1], JOINTS[name][2]


LOOKS = {
    "faithful": dict(label="A: today's hermit, redrawn", skin="#c99a72", skin_lt="#e3bb93", skin_sh="#a07352", skin_dk="#7d5440",
                     far="#ad7f5c", nose="#cf8e6a", rag="#ddd2b4", rag_sh="#b1a585", rag_lt="#f0e8d0", shorts="#4d4049",
                     shorts_sh="#362c33", shorts_lt="#6e5e68", stache="#4b3a2f", stache_lt="#6e5747", hair=None, rope="#9a7a52",
                     eyes="mismatch"),
    "sunbaked": dict(label="B: sun-baked, red rag, wiry grey", skin="#a86d48", skin_lt="#c98e63", skin_sh="#835136", skin_dk="#5f3826",
                     far="#8f5a3b", nose="#b8694a", rag="#b7432f", rag_sh="#8a2f20", rag_lt="#d4644c", shorts="#5b6a3a",
                     shorts_sh="#414c28", shorts_lt="#7a8a50", stache="#b9b2a6", stache_lt="#e2ddd3", hair="#c7c1b5", rope="#7a5a36",
                     eyes="mismatch", patch="#c9a46a"),
    "cave": dict(label="C: pale cave hermit, long white moustache", skin="#d8c3b0", skin_lt="#efe1d2", skin_sh="#b39985", skin_dk="#8c7362",
                 far="#bda895", nose="#d6a896", rag="#7b7f84", rag_sh="#5a5e63", rag_lt="#9ca1a7", shorts="#6a4e37",
                 shorts_sh="#4c3626", shorts_lt="#8a6a4d", stache="#eeeae2", stache_lt="#ffffff", hair="#eeeae2", rope="#5b4a3a",
                 eyes="stare", long_stache=True),
}


def outlined(sil, fill, items=(), cid=None, width=None):
    body = [path(sil, fill)]
    if items:
        body = clipped(cid, sil, [path(sil, fill)] + list(items))
    return body + [path(sil, "none", INK, width or 2 * OW)]


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def limb(a, b, r0, r1, fill, sh, lt, cid):
    ux, uy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(ux, uy)
    nx, ny = -uy / d, ux / d
    s = 1 if ny > 0 else -1
    items = [line([(a[0] + nx * r0 * 0.6 * s, a[1] + ny * r0 * 0.6 * s), (b[0] + nx * r1 * 0.6 * s, b[1] + ny * r1 * 0.6 * s)], sh, 3.2)]
    if lt:
        items.append(line([(a[0] - nx * r0 * 0.4 * s, a[1] - ny * r0 * 0.4 * s), (b[0] - nx * r1 * 0.4 * s, b[1] - ny * r1 * 0.4 * s)], lt, 1.6))
    return outlined(capsule(a, b, r0, r1), fill, items, cid)


def hand(o, wr, el, near, cid):
    """A bony hand with four long fingers, hanging forward of the wrist."""
    fill = o["skin"] if near else o["far"]
    ang = math.atan2(wr[1] - el[1], wr[0] - el[0]) - 0.35
    ux, uy = math.cos(ang), math.sin(ang)
    nx, ny = -uy, ux
    p = lambda t, s: (wr[0] + ux * t + nx * s, wr[1] + uy * t + ny * s)
    out = []
    for k, (spread, length) in enumerate(((-5.0, 30), (-1.7, 34), (1.7, 32), (5.0, 26))):
        a, b = p(8, spread * 0.8), p(8 + length, spread * 1.8 + 3)
        # Each finger clips its crease to its own outline: one id per finger.
        out += outlined(capsule(a, b, 2.8, 2.0), fill, [line([lerp(a, b, 0.45), lerp(a, b, 0.5)], o["skin_dk"], 1.0)], f"{cid}-f{k}", 1.1)
    palm = smooth([p(-2, -7), p(10, -8), p(13, 0), p(10, 8), p(-2, 7)])
    out += outlined(palm, fill, [path(smooth([p(-2, 2), p(12, 2), p(9, 7), p(-2, 6)]), o["skin_sh"])], cid)
    thumb_a, thumb_b = p(4, 6), p(14, 12)
    out += outlined(capsule(thumb_a, thumb_b, 2.8, 2.0), fill, [], None, 1.1)
    return out

#: His curse, sneezed and jabbed: a sickly green.
for _look in LOOKS.values():
    _look.setdefault("curse", "#74dcb0")
    _look.setdefault("curse_core", "#c8f7d4")


def head(o):
    out = []
    # the rag's knot and tails at the back, behind the skull
    out += outlined(smooth([(292, 206), (276, 196), (262, 204, True), (270, 214), (262, 232, True), (280, 222), (294, 218)]),
                    o["rag"], [path(smooth([(276, 214), (262, 232), (280, 222)]), o["rag_sh"])], "c-tails")
    skull = smooth([(296, 230), (294, 206), (304, 192), (322, 186), (340, 192), (348, 206), (348, 226), (342, 244), (334, 256),
                    (322, 262), (308, 260), (298, 248)])
    items = [path(smooth([(298, 236), (346, 232), (342, 262), (300, 262)]), o["skin_sh"]),
             path(smooth([(316, 196), (336, 196), (342, 210), (326, 208)]), o["skin_lt"]),
             # wrinkles on the brow and the hollow of the cheek
             line([(330, 206), (342, 204)], o["skin_dk"], 1.1), line([(328, 210), (340, 209)], o["skin_dk"], 0.9),
             line([(320, 236), (326, 248)], o["skin_dk"], 1.2)]
    out += outlined(skull, o["skin"], items, "c-skull")
    if o.get("hair"):
        for a, b in (((298, 214), (286, 222)), ((298, 222), (284, 232)), ((300, 230), (288, 240)), ((302, 236), (292, 248))):
            out.append(line([a, lerp(a, b, 0.5), b], o["hair"], 2.4))
    # the ear, big and low
    out += outlined(smooth([(304, 216), (312, 214), (314, 226), (310, 236), (302, 234), (300, 224)]), o["skin"],
                    [line([(306, 220), (309, 228), (305, 232)], o["skin_dk"], 1.2)], "c-ear")
    # the rag over the crown, low on the brow
    rag = smooth([(294, 214), (298, 196), (312, 184), (330, 180), (346, 186), (352, 198), (350, 206), (330, 204), (312, 208), (300, 216)])
    out += outlined(rag, o["rag"], [path(smooth([(294, 214), (350, 202), (350, 208), (300, 218)]), o["rag_sh"]),
                                    path(smooth([(312, 186), (330, 182), (340, 188), (322, 192)]), o["rag_lt"]),
                                    line([(318, 190), (324, 202)], o["rag_sh"], 1.0)], "c-rag")
    # the nose: absurdly long, drooping, a bulb at the end
    nose = smooth([(342, 218), (356, 222), (370, 230), (382, 242), (384, 252), (376, 258), (366, 254), (352, 244), (342, 236)])
    out += outlined(nose, o["nose"], [path(smooth([(346, 232), (372, 246), (376, 258), (360, 254), (344, 240)]), o["skin_sh"]),
                                      path(smooth([(352, 224), (368, 232), (372, 238), (356, 230)]), o["skin_lt"]),
                                      ellipse(370, 252, 2.2, 1.4, o["skin_dk"])], "c-nose")
    # the moustache under it
    if o.get("long_stache"):
        st = smooth([(338, 244), (356, 248), (360, 262), (352, 290), (346, 310, True), (342, 288), (336, 268), (330, 256)])
    else:
        st = smooth([(334, 244), (352, 246), (362, 254), (360, 268, True), (352, 260), (344, 262), (336, 258), (330, 252)])
    out += outlined(st, o["stache"], [line([(340, 250), (348, 262)], o["stache_lt"], 1.2), line([(346, 250), (354, 262)], o["stache_lt"], 1.0)], "c-stache")
    return out


TORSO = [(294, 246), (276, 248), (256, 262), (242, 290), (238, 326), (242, 356), (262, 364), (290, 362), (306, 348), (308, 326),
         (302, 300), (304, 276), (310, 262)]


def torso(o):
    sil = smooth(TORSO)
    items = [path(smooth([(240, 300), (256, 274), (262, 300), (256, 350), (240, 350)]), o["skin_sh"]),
             path(smooth([(284, 254), (298, 252), (300, 270), (288, 270)]), o["skin_lt"]),
             # collarbone, three ribs, the pot of the belly and its wrinkles, the navel
             line([(288, 262), (302, 268)], o["skin_dk"], 1.2),
             line([(286, 276), (300, 280)], o["skin_dk"], 1.0), line([(284, 284), (298, 289)], o["skin_dk"], 1.0),
             line([(284, 292), (296, 298)], o["skin_dk"], 0.9),
             path(smooth([(296, 310), (308, 322), (308, 344), (296, 352), (300, 330)]), o["skin_sh"]),
             line([(290, 326), (300, 330)], o["skin_dk"], 0.9), line([(288, 336), (300, 340)], o["skin_dk"], 0.9),
             ellipse(300, 336, 1.4, 1.8, o["skin_dk"]),
             # the knobs of his spine down the hump
             ellipse(262, 266, 2.0, 1.6, o["skin_dk"]), ellipse(252, 280, 2.0, 1.6, o["skin_dk"]), ellipse(246, 296, 2.0, 1.6, o["skin_dk"])]
    out = [path(capsule((296, 262), (312, 236), 9.0, 8.0), o["skin"], INK, 2 * OW),  # the neck, thrust forward
           line([(304, 252), (310, 244)], o["skin_dk"], 1.1)]
    out += outlined(sil, o["skin"], items, "c-torso")
    # the shorts: baggy, a rope belt, a patch
    sh = smooth([(240, 344), (308, 340), (314, 360), (310, 384), (290, 390), (266, 386), (244, 388), (236, 368)])
    items = [path(smooth([(236, 364), (256, 360), (260, 390), (236, 390)]), o["shorts_sh"]),
             path(smooth([(286, 352), (308, 350), (310, 360), (290, 362)]), o["shorts_lt"]),
             line([(276, 362), (280, 388)], o["shorts_sh"], 1.2)]
    if o.get("patch"):
        items.append(path(smooth([(290, 368, True), (304, 366, True), (305, 380, True), (291, 381, True)]), o["patch"], INK, 1.0))
        items.append(line([(292, 370), (302, 378)], o["shorts_sh"], 0.8))
    else:
        items.append(path(smooth([(290, 368, True), (304, 366, True), (305, 380, True), (291, 381, True)]), o["shorts_lt"], INK, 1.0))
    out += outlined(sh, o["shorts"], items, "c-shorts")
    out.append(line([(238, 348), (272, 346), (310, 342)], INK, 4.2))
    out.append(line([(238, 348), (272, 346), (310, 342)], o["rope"], 2.4))
    out += [line([(306, 344), (312, 360)], o["rope"], 2.0), line([(304, 344), (306, 362)], o["rope"], 2.0)]
    return out




def eyes(o, kind):
    """One set of eyes (the rig shows one at a time)."""
    if kind == "open":
        out = []
        if o["eyes"] == "mismatch":
            out += [path(smooth([(334, 214), (339, 210), (345, 212), (344, 218), (338, 219)]), "#f4ead2", INK, 1.2),
                    ellipse(341, 214.5, 1.9, 2.2, INK),
                    line([(330, 209), (338, 206), (346, 208)], o["stache"], 2.6)]
        else:
            out += [ellipse(339, 214, 6.0, 6.4, "#f4ead2", INK, 1.3), ellipse(341, 214, 2.4, 2.6, INK), ellipse(340, 213, 0.8, 0.8, "#ffffff"),
                    line([(331, 205), (339, 203), (347, 206)], o["stache"], 2.6)]
        return out
    if kind == "shut":
        return [line([(332, 214), (339, 216.5), (346, 213)], INK, 1.8), line([(330, 208), (338, 206), (346, 208)], o["stache"], 2.6)]
    return [line([(335, 210), (345, 219)], INK, 1.8), line([(335, 219), (345, 210)], INK, 1.8)]


def thigh(o, side):
    near = side == "near"
    fill = o["skin"] if near else o["far"]
    hip, knee = P(f"{side}_leg_u"), P(f"{side}_leg_l")
    return limb(lerp(hip, knee, 0.3), knee, 7.0, 6.0, fill, o["skin_sh"], o["skin_lt"] if near else None, f"c-{side}-th")


def shin(o, side):
    near = side == "near"
    fill = o["skin"] if near else o["far"]
    knee, ankle = P(f"{side}_leg_l"), P(f"{side}_foot")
    out = limb(knee, ankle, 6.0, 4.6, fill, o["skin_sh"], o["skin_lt"] if near else None, f"c-{side}-sh")
    out += outlined(smooth([(knee[0] - 6, knee[1] - 3), (knee[0] + 2, knee[1] - 8), (knee[0] + 9, knee[1] - 2), (knee[0] + 6, knee[1] + 7), (knee[0] - 3, knee[1] + 6)]),
                    fill, [path(smooth([(knee[0] - 6, knee[1] + 2), (knee[0] + 9, knee[1] + 1), (knee[0] + 6, knee[1] + 7), (knee[0] - 3, knee[1] + 6)]), o["skin_sh"])], f"c-{side}-knee")
    return out


def foot(o, side):
    near = side == "near"
    fill = o["skin"] if near else o["far"]
    ax, ay = P(f"{side}_foot")
    shape = smooth([(ax - 8, ay - 6), (ax + 4, ay - 4), (ax + 18, ay + 4), (ax + 32, ay + 8), (ax + 36, ay + 14, True), (ax + 2, ay + 18, True),
                    (ax - 10, ay + 16), (ax - 12, ay + 6)])
    items = [path(smooth([(ax - 12, ay + 12), (ax + 36, ay + 12), (ax + 36, ay + 18), (ax - 12, ay + 18)]), o["skin_sh"])]
    for k in range(3):
        items.append(line([(ax + 22 + k * 4, ay + 9 + k * 0.6), (ax + 24 + k * 4, ay + 15)], o["skin_dk"], 1.0))
    return outlined(shape, fill, items, f"c-{side}-foot")


def upper_arm(o, side):
    near = side == "near"
    fill = o["skin"] if near else o["far"]
    return limb(P(f"{side}_arm_u"), P(f"{side}_arm_l"), 6.5, 5.0, fill, o["skin_sh"], o["skin_lt"] if near else None, f"c-{side}-ua")


def forearm(o, side):
    near = side == "near"
    fill = o["skin"] if near else o["far"]
    el, wr = P(f"{side}_arm_l"), P(f"{side}_hand")
    out = limb(el, wr, 5.0, 4.0, fill, o["skin_sh"], o["skin_lt"] if near else None, f"c-{side}-fa")
    out.append(ellipse(el[0], el[1], 5.6, 5.6, fill, INK, 1.4 * OW))
    return out


def jab_fx(o):
    """A crackle off his fingertips (``fx_jab``)."""
    wx, wy = P("near_hand")
    tip = (wx + 40, wy + 12)
    out = []
    for k, (dx, dy) in enumerate(((14, -8), (16, 4), (10, 14))):
        out.append(line([tip, (tip[0] + dx * 0.5, tip[1] + dy * 0.5 - 2), (tip[0] + dx, tip[1] + dy)], o["curse"], 2.4))
    out.append(ellipse(tip[0], tip[1], 4.0, 4.0, o["curse_core"]))
    return out


def grab_fx(o):
    """The swipe of his clutching fingers (``fx_grab``)."""
    wx, wy = P("near_hand")
    return [path(smooth([(wx + 20, wy - 30), (wx + 50, wy - 4), (wx + 44, wy + 30), (wx + 34, wy + 4)]), o["curse"])]


def sneeze_fx(o):
    """The curse he sneezes: a green plume off the end of his nose (``fx_sneeze``)."""
    out = []
    for k, (x, y, r) in enumerate(((396, 252, 9), (414, 246, 11), (434, 252, 13), (452, 244, 10))):
        out.append(ellipse(x, y, r, r * 0.85, o["curse"]))
        out.append(ellipse(x - r * 0.25, y - r * 0.25, r * 0.45, r * 0.4, o["curse_core"]))
    return out


#: The parts, in the order they are drawn: (group id, label, part, bone, z, opacity channel).
LAYERS = [
    ("far-arm-upper", "Far Arm - Upper", "far_arm_u", "far_arm_u", 4, ""),
    ("far-arm-lower", "Far Arm - Lower", "far_arm_l", "far_arm_l", 5, ""),
    ("far-hand", "Far Hand", "far_hand", "far_hand", 6, ""),
    ("far-thigh", "Far Thigh", "far_leg_u", "far_leg_u", 8, ""),
    ("far-shin", "Far Shin", "far_leg_l", "far_leg_l", 9, ""),
    ("far-foot", "Far Foot", "far_foot", "far_foot", 10, ""),
    ("near-thigh", "Near Thigh", "near_leg_u", "near_leg_u", 12, ""),
    ("near-shin", "Near Shin", "near_leg_l", "near_leg_l", 13, ""),
    ("near-foot", "Near Foot", "near_foot", "near_foot", 14, ""),
    ("torso", "Torso and Shorts", "torso", "torso", 20, ""),
    ("head", "Head", "head", "head", 26, ""),
    ("eye-open", "Eyes - Open", "eye_open", "head", 27, "eye_open"),
    ("eye-shut", "Eyes - Shut", "eye_shut", "head", 27, "eye_shut"),
    ("eye-dead", "Eyes - Dead", "eye_dead", "head", 27, "eye_dead"),
    ("fx-sneeze", "FX - Sneeze", "fx_sneeze", "head", 28, "fx_sneeze"),
    ("near-arm-upper", "Near Arm - Upper", "near_arm_u", "near_arm_u", 30, ""),
    ("near-arm-lower", "Near Arm - Lower", "near_arm_l", "near_arm_l", 31, ""),
    ("near-hand", "Near Hand", "near_hand", "near_hand", 32, ""),
    ("fx-jab", "FX - Jab", "fx_jab", "near_hand", 33, "fx_jab"),
    ("fx-grab", "FX - Grab", "fx_grab", "near_hand", 33, "fx_grab"),
]


def drawn(o) -> Dict[str, list]:
    out = {"torso": torso(o), "head": head(o), "eye-open": eyes(o, "open"), "eye-shut": eyes(o, "shut"),
           "eye-dead": eyes(o, "dead"), "fx-sneeze": sneeze_fx(o), "fx-jab": jab_fx(o), "fx-grab": grab_fx(o)}
    for side in ("far", "near"):
        out[f"{side}-arm-upper"] = upper_arm(o, side)
        out[f"{side}-arm-lower"] = forearm(o, side)
        out[f"{side}-hand"] = hand(o, P(f"{side}_hand"), P(f"{side}_arm_l"), side == "near", f"c-{side}-hand")
        out[f"{side}-thigh"] = thigh(o, side)
        out[f"{side}-shin"] = shin(o, side)
        out[f"{side}-foot"] = foot(o, side)
    return out


def svg_text(look: str = LOOK) -> str:
    o = LOOKS[look]
    svg.configure(dx=0, dy=0, ink=INK, ow=OW, colors={})
    parts = drawn(o)
    svg.PARTS.clear()
    for group, label, name, bone, z, channel in LAYERS:
        extra = (f' data-rig-opacity="{channel}"' + (' data-rig-default="1"' if channel == "eye_open" else "")) if channel else ""
        part(group, label, name, bone, z, parts[group], extra)
    note = ("the Weird Hermit's look (Jon chose B, 2026-10-18)" if look == LOOK
            else "KEPT, NOT CAST: a hermit look Jon kept (2026-10-18), not registered in the cast")
    return svg.document(
        size=(W, H), design=f"weird-hermit-{look}", layer_id="weird-hermit", label=VIEW,
        comment=[f"  <!-- {note}: side view facing right, the ground at y=470.",
                 "       Drawn by scripts/svg_art/weird_hermit_art.py; each part turns about its JOINTS entry. -->"],
        joints=svg.joints_layer({k: (v[1], v[2]) for k, v in JOINTS.items()}),
    )


def main() -> None:
    if len(sys.argv) > 2 and sys.argv[1] == "--all":
        out = Path(sys.argv[2])
        out.mkdir(parents=True, exist_ok=True)
        for look in LOOKS:
            (out / f"weird_hermit_{look}.svg").write_text(svg_text(look), encoding="utf8")
            print(out / f"weird_hermit_{look}.svg")
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".svg.tmp")
    tmp.write_text(svg_text(), encoding="utf8")
    tmp.replace(OUT)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
