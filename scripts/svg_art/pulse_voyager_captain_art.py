#!/usr/bin/env python3
"""How Captain Pulse's SVG was first drawn (reference, not authority).

    uv run python scripts/svg_art/pulse_voyager_captain_art.py

Writes ``data/characters/pulse_voyager_captain/pulse_voyager_captain.svg``;
the SVG owns the art after this has run once. ``JOINTS`` says where each part
turns and ``LAYERS`` lists the parts; ``scripts/build_pulse_voyager_captain_rig.py``
reads both and authors the rows.

Jon, 2026-10-18: "if I had to ask you to redesign the main character what
would it look like?", then "refine that and then use that to replace a
different robot character (captain something?)". So this is Claude's own
redesign of the v2 robot (not the traced v3): the v2 box head, dark visor,
oval eyes, light muzzle and one rigid antenna kept, built as white shell
plates over a dark jointed suit, cel-shaded under a thin ink. Captain Pulse
wears it in the Pulse Voyagers' colours ("cyan voyage glow / winglets /
comet trails"): a navy hull with a comet badge, gold shoulder boards, swept
winglets at the ear and the heels, and a comet trail when he runs or dashes.
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
OUT = ROOT / "ambition_sprite2d_renderer" / "data" / "characters" / "pulse_voyager_captain" / "pulse_voyager_captain.svg"
VIEW = "Captain Pulse - Side Right"
W, H = 560, 560
INK = "#141820"
OW = 1.8

C = dict(
    shell="#f4f5f7", shell_lt="#ffffff", shell_sh="#ccd2db", shell_dk="#a8b0bc", far="#d5dae1", far_sh="#b2b9c3",
    muzzle="#e5e9ef", suit="#2a3140", suit_lt="#46506a", suit_dk="#1b202b",
    hull="#24386a", hull_lt="#3a5594", hull_sh="#18264a",
    glass="#0e141b", glass_lt="#24313d", glare="#6b8aa0",
    cyan="#3be8ff", cyan_lt="#d8fbff", cyan_dk="#169bb5",
    gold="#f2c14e", gold_dk="#a87d1e",
)

#: The ground, in SVG units: the rig's frame puts it on its ground line.
GROUND_Y = 470.0
#: Where each bone turns (SVG units): ``bone: (parent, x, y)``, parents first.
JOINTS: Dict[str, Tuple[str, float, float]] = {
    "body": ("", 262.0, 396.0),
    "torso": ("body", 262.0, 382.0),
    "head": ("torso", 262.0, 294.0),
    "near_arm_upper": ("torso", 290.0, 316.0),
    "near_arm_lower": ("near_arm_upper", 296.0, 348.0),
    "near_hand": ("near_arm_lower", 300.0, 376.0),
    "far_arm_upper": ("torso", 234.0, 314.0),
    "far_arm_lower": ("far_arm_upper", 228.0, 346.0),
    "far_hand": ("far_arm_lower", 230.0, 374.0),
    "near_leg": ("body", 272.0, 400.0),
    "near_shin": ("near_leg", 274.0, 428.0),
    "near_foot": ("near_shin", 272.0, 452.0),
    "far_leg": ("body", 250.0, 398.0),
    "far_shin": ("far_leg", 250.0, 428.0),
    "far_foot": ("far_shin", 246.0, 452.0),
}


def P(name: str) -> Tuple[float, float]:
    return JOINTS[name][1], JOINTS[name][2]


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def outlined(sil, fill, items=(), cid=None, width=None):
    """A filled shape, its shading clipped inside it, then its outline."""
    body = [path(sil, fill)]
    if items:
        body = clipped(cid, sil, [path(sil, fill)] + list(items))
    return body + [path(sil, "none", INK, width or 2 * OW)]


def rrect(x0, y0, x1, y1, r):
    return smooth([(x0 + r, y0), (x1 - r, y0), (x1, y0 + r), (x1, y1 - r), (x1 - r, y1), (x0 + r, y1), (x0, y1 - r), (x0, y0 + r)])


def lit(pts, fill, sh, lt, cid, d=(5.0, 6.0)):
    """A shell plate: shaded down and back, lit up and forward."""
    sil = smooth(pts)
    items = [path(sil, sh), path(smooth([(q[0] - d[0], q[1] - d[1]) + tuple(q[2:]) for q in pts]), fill)]
    if lt:
        items.append(path(smooth([(q[0] - d[0] * 2.2, q[1] - d[1] * 2.2) + tuple(q[2:]) for q in pts[: len(pts) // 2]] +
                                 [(q[0] - d[0] * 1.2, q[1] - d[1] * 1.2) for q in pts[: len(pts) // 2][::-1]]), lt))
    return outlined(sil, fill, items, cid)


def plate(a, b, r0, r1, near, cid, fill=None, sh=None):
    """A limb plate between two points, lit on its upper edge."""
    fill = fill or (C["shell"] if near else C["far"])
    sh = sh or (C["shell_sh"] if near else C["far_sh"])
    ux, uy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(ux, uy)
    nx, ny = -uy / d, ux / d
    s = 1 if ny > 0 else -1
    items = [line([(a[0] + nx * r0 * 0.62 * s, a[1] + ny * r0 * 0.62 * s), (b[0] + nx * r1 * 0.62 * s, b[1] + ny * r1 * 0.62 * s)], sh, 5.0),
             line([(a[0] - nx * r0 * 0.42 * s, a[1] - ny * r0 * 0.42 * s), (b[0] - nx * r1 * 0.42 * s, b[1] - ny * r1 * 0.42 * s)],
                  C["shell_lt"] if near else C["shell"], 2.2)]
    return outlined(capsule(a, b, r0, r1), fill, items, cid)


def joint(c, r, near):
    return [ellipse(c[0], c[1], r, r, C["suit"] if near else C["suit_dk"], INK, 2 * OW),
            ellipse(c[0] - r * 0.25, c[1] - r * 0.25, r * 0.42, r * 0.42, C["suit_lt"])]


# --- head ----------------------------------------------------------------------------------
#: v2's box, a little wider at the brow than the jaw.
HEAD = [(198, 198), (208, 178), (232, 168), (298, 168), (320, 178), (332, 200), (332, 260), (324, 280), (302, 292),
        (228, 292), (208, 284), (200, 264)]
EYES = ((284.0, 232.0, 9.0, 14.0), (316.0, 232.0, 8.0, 13.0))


def head_part():
    sil = smooth(HEAD)
    items = [path(sil, C["shell_sh"]), path(smooth([(q[0] - 5, q[1] - 6) for q in HEAD]), C["shell"]),
             path(smooth([(208, 196), (224, 178), (266, 174), (238, 186), (216, 206), (210, 226)]), C["shell_lt"]),
             # v2's light muzzle, as a face plate under the visor
             path(smooth([(252, 264), (330, 262), (330, 280), (320, 290), (264, 290), (250, 280)]), C["muzzle"]),
             line([(244, 176), (240, 230), (246, 290)], C["shell_dk"], 1.6)]
    body = outlined(sil, C["shell"], items, "clip-head")
    # the visor, a little proud of the face, with a glare
    body += outlined(rrect(252, 202, 340, 262, 18), C["glass"],
                     [line([(260, 254), (270, 210)], C["glare"], 3.0), line([(270, 256), (276, 238)], C["glass_lt"], 2.0)], "clip-visor")
    # the ear: a socket under a swept winglet, the one rigid antenna above it
    body.append(path(smooth([(214, 226), (196, 214), (166, 206, True), (184, 226), (200, 248), (214, 244)]), C["shell"], INK, 2 * OW))
    body.append(line([(198, 222), (176, 212)], C["cyan"], 2.4))
    body.append(ellipse(222, 232, 15.0, 17.0, C["shell"], INK, 2 * OW))
    body.append(ellipse(222, 232, 9.0, 10.5, C["hull"], INK, 1.4))
    body.append(ellipse(222, 232, 4.0, 4.5, C["cyan"]))
    body.append(line([(226, 170), (222, 142)], INK, 6.0))
    body.append(line([(226, 170), (222, 142)], C["shell_dk"], 3.0))
    body.append(ellipse(221.5, 136, 9.0, 9.0, C["cyan"], INK, 2 * OW))
    body.append(ellipse(218.5, 132.5, 3.0, 3.0, C["cyan_lt"]))
    return body


def eyes(kind: str):
    """One set of eyes on the visor (the rig shows one set at a time)."""
    out = []
    for x, y, rx, ry in EYES:
        if kind == "open":
            out += [ellipse(x, y, rx, ry, C["cyan"]), ellipse(x + 1.5, y + 4, rx * 0.55, ry * 0.5, C["cyan_dk"]),
                    ellipse(x - 2.5, y - 6, rx * 0.35, ry * 0.25, C["cyan_lt"])]
        elif kind == "shut":
            out.append(line([(x - rx, y + 2), (x, y + 5), (x + rx, y + 2)], C["cyan"], 3.4))
        elif kind == "happy":
            out.append(line([(x - rx, y + 4), (x, y - 6), (x + rx, y + 4)], C["cyan"], 3.6))
        elif kind == "hurt":
            out.append(line([(x - rx, y - 6), (x + rx * 0.6, y), (x - rx, y + 6)], C["cyan"], 3.4))
        else:  # dead
            out += [line([(x - rx * 0.8, y - 7), (x + rx * 0.8, y + 7)], C["cyan_dk"], 3.4),
                    line([(x - rx * 0.8, y + 7), (x + rx * 0.8, y - 7)], C["cyan_dk"], 3.4)]
    return out


def talk_mouth():
    """A little level meter under the eyes, lit while he talks."""
    return [path(rrect(286 + i * 9, 252 - h, 292 + i * 9, 256, 1.5), C["cyan"]) for i, h in enumerate((4, 8, 5))]


# --- torso and hips -------------------------------------------------------------------------
TORSO = [(226, 306), (240, 296), (282, 296), (298, 308), (302, 336), (296, 360), (282, 372), (240, 372), (226, 360), (220, 334)]
PELVIS = [(236, 384), (290, 382), (294, 394), (288, 408), (240, 410), (232, 396)]


def torso_part():
    body = [path(capsule((262, 282), (262, 302), 11.0, 12.0), C["suit"], INK, 2 * OW)]
    sil = smooth(TORSO)
    items = [path(sil, C["hull_sh"]), path(smooth([(q[0] - 4, q[1] - 6) for q in TORSO]), C["hull"]),
             path(smooth([(230, 312), (246, 302), (272, 300), (248, 312), (236, 330)]), C["hull_lt"]),
             # a white collar plate, and the hull's lower band
             path(smooth([(238, 296), (284, 296), (296, 306), (262, 312), (232, 306)]), C["shell"]),
             line([(232, 352), (296, 350)], C["hull_sh"], 1.6)]
    body += outlined(sil, C["hull"], items, "clip-torso")
    # the comet badge on the chest: v2's chest panel, as rank
    body += [path(smooth([(256, 336), (246, 344), (234, 352, True), (246, 336), (254, 326)]), C["cyan_dk"]),
             ellipse(264, 326, 8.0, 8.0, C["cyan"], INK, 1.6), ellipse(262, 324, 2.6, 2.6, C["cyan_lt"])]
    return body


def hips_part():
    body = [path(capsule((262, 364), (262, 388), 20.0, 20.0), C["suit"], INK, 2 * OW),
            line([(246, 376), (278, 376)], C["suit_lt"], 1.6)]
    body += lit(PELVIS, C["shell"], C["shell_sh"], None, "clip-pelvis", (3.0, 5.0))
    body.append(path(rrect(256, 386, 270, 398, 3), C["cyan"], INK, 1.2))
    return body


def trail_part():
    """The comet trail behind him (``fx_trail``): run and dash light it."""
    out = []
    for k, (y, length, w) in enumerate(((440, 150, 10.0), (414, 120, 7.0), (388, 90, 5.0))):
        x0 = 236 - k * 4
        out.append(path(smooth([(x0, y - w), (x0 - length * 0.6, y - w * 0.5), (x0 - length, y, True), (x0 - length * 0.6, y + w * 0.5), (x0, y + w)]),
                        C["cyan"] if k == 0 else C["cyan_dk"]))
        out.append(path(smooth([(x0, y - w * 0.4), (x0 - length * 0.55, y), (x0, y + w * 0.4)]), C["cyan_lt"]))
    return out


# --- limbs ---------------------------------------------------------------------------------
def shoulder_cap(sh, near):
    fill = C["shell"] if near else C["far"]
    cap = smooth([(sh[0] - 15, sh[1] + 4), (sh[0] - 12, sh[1] - 10), (sh[0], sh[1] - 15), (sh[0] + 13, sh[1] - 10), (sh[0] + 16, sh[1] + 4), (sh[0], sh[1] + 9)])
    out = outlined(cap, fill, [path(smooth([(sh[0] - 15, sh[1] + 4), (sh[0] + 16, sh[1] + 4), (sh[0] + 16, sh[1] + 12), (sh[0] - 15, sh[1] + 12)]),
                                    C["shell_sh"] if near else C["far_sh"])], f"c-cap-{near}")
    # gold shoulder boards: the captain's rank
    out.append(path(rrect(sh[0] - 12, sh[1] - 13, sh[0] + 12, sh[1] - 7, 2.5), C["gold"] if near else C["gold_dk"], INK, 1.2))
    for k in (-6, 0, 6):
        out.append(line([(sh[0] + k, sh[1] - 12), (sh[0] + k, sh[1] - 8)], C["gold_dk"], 1.2))
    return out


def arm_parts(side):
    near = side == "near"
    sh, el, wr = P(f"{side}_arm_upper"), P(f"{side}_arm_lower"), P(f"{side}_hand")
    suit = C["suit"] if near else C["suit_dk"]
    upper = [path(capsule(sh, el, 7.0, 6.5), suit, INK, 2 * OW)] + plate(lerp(sh, el, 0.25), lerp(sh, el, 0.85), 10.0, 9.0, near, f"c-{side}-ua")
    upper += shoulder_cap(sh, near)
    lower = [path(capsule(el, wr, 6.5, 6.0), suit, INK, 2 * OW)] + plate(lerp(el, wr, 0.3), lerp(el, wr, 0.9), 8.5, 10.0, near, f"c-{side}-fa")
    lower += joint(el, 7.5, near)
    lower.append(path(rrect(wr[0] - 10, wr[1] - 6, wr[0] + 10, wr[1] - 2, 1.5), C["cyan"] if near else C["cyan_dk"]))
    wx, wy = wr
    fill = C["shell"] if near else C["far"]
    # A mitten hand hanging from the wrist, fingers down.
    hand = smooth([(wx - 9, wy - 2), (wx + 8, wy - 3), (wx + 11, wy + 8), (wx + 9, wy + 18), (wx + 1, wy + 21), (wx - 8, wy + 16), (wx - 10, wy + 6)])
    hb = outlined(hand, fill, [line([(wx - 8, wy + 10), (wx + 10, wy + 10)], C["suit"], 1.6),
                               path(smooth([(wx - 10, wy + 12), (wx + 11, wy + 12), (wx + 9, wy + 22), (wx - 9, wy + 22)]),
                                    C["shell_sh"] if near else C["far_sh"])], f"c-{side}-hand")
    return upper, lower, hb


def leg_parts(side):
    near = side == "near"
    hip, knee, ankle = P(f"{side}_leg"), P(f"{side}_shin"), P(f"{side}_foot")
    suit = C["suit"] if near else C["suit_dk"]
    thigh = [path(capsule(hip, knee, 8.0, 7.5), suit, INK, 2 * OW)] + plate(lerp(hip, knee, 0.15), lerp(hip, knee, 0.78), 13.0, 12.0, near, f"c-{side}-th")
    shin = [path(capsule(knee, ankle, 7.5, 7.0), suit, INK, 2 * OW)] + plate(lerp(knee, ankle, 0.3), lerp(knee, ankle, 0.92), 11.5, 10.5, near, f"c-{side}-sh")
    shin += joint(knee, 8.0, near)
    ax, ay = ankle
    fill = C["shell"] if near else C["far"]
    boot = smooth([(ax - 15, ay - 6), (ax + 4, ay - 10), (ax + 18, ay - 4), (ax + 30, ay + 4), (ax + 32, ay + 12),
                   (ax + 32, ay + 18, True), (ax - 17, ay + 18, True), (ax - 18, ay + 6)])
    items = [path(smooth([(ax - 22, ay + 11, True), (ax + 36, ay + 11, True), (ax + 36, ay + 20, True), (ax - 22, ay + 20, True)]), C["suit_dk"]),
             path(smooth([(ax - 22, ay + 8, True), (ax + 36, ay + 8, True), (ax + 36, ay + 11.5, True), (ax - 22, ay + 11.5, True)]),
                  C["cyan"] if near else C["cyan_dk"]),
             path(smooth([(ax - 13, ay - 4), (ax + 2, ay - 8), (ax - 2, ay + 2), (ax - 13, ay + 4)]), C["shell_lt"] if near else C["far"])]
    # a heel winglet
    foot = [path(smooth([(ax - 12, ay + 2), (ax - 26, ay - 6), (ax - 36, ay - 10, True), (ax - 26, ay + 4), (ax - 14, ay + 10)]), fill, INK, 2 * OW)]
    foot += outlined(boot, fill, items, f"c-{side}-boot")
    return thigh, shin, foot


#: The parts, in the order they are drawn: (group id, label, part, bone, z, opacity channel).
LAYERS = [
    ("trail", "FX - Comet Trail", "fx_trail", "body", 1, "fx_trail"),
    ("far-arm-upper", "Far Arm - Upper", "far_arm_upper", "far_arm_upper", 4, ""),
    ("far-arm-lower", "Far Arm - Lower", "far_arm_lower", "far_arm_lower", 5, ""),
    ("far-hand", "Far Hand", "far_hand", "far_hand", 6, ""),
    ("far-leg", "Far Thigh", "far_leg", "far_leg", 8, ""),
    ("far-shin", "Far Shin", "far_shin", "far_shin", 9, ""),
    ("far-foot", "Far Boot", "far_foot", "far_foot", 10, ""),
    ("near-leg", "Near Thigh", "near_leg", "near_leg", 12, ""),
    ("near-shin", "Near Shin", "near_shin", "near_shin", 13, ""),
    ("near-foot", "Near Boot", "near_foot", "near_foot", 14, ""),
    ("hips", "Hips", "hips", "body", 18, ""),
    ("torso", "Hull", "torso", "torso", 20, ""),
    ("head", "Head", "head", "head", 26, ""),
    ("eye-open", "Eyes - Open", "eye_open", "head", 27, "eye_open"),
    ("eye-shut", "Eyes - Shut", "eye_shut", "head", 27, "eye_shut"),
    ("eye-happy", "Eyes - Happy", "eye_happy", "head", 27, "eye_happy"),
    ("eye-hurt", "Eyes - Hurt", "eye_hurt", "head", 27, "eye_hurt"),
    ("eye-dead", "Eyes - Dead", "eye_dead", "head", 27, "eye_dead"),
    ("mouth-talk", "Visor - Talking", "mouth_talk", "head", 28, "mouth_talk"),
    ("near-arm-upper", "Near Arm - Upper", "near_arm_upper", "near_arm_upper", 30, ""),
    ("near-arm-lower", "Near Arm - Lower", "near_arm_lower", "near_arm_lower", 31, ""),
    ("near-hand", "Near Hand", "near_hand", "near_hand", 32, ""),
]


def drawn() -> Dict[str, list]:
    svg.configure(dx=0, dy=0, ink=INK, ow=OW, colors=C)
    out = {"trail": trail_part(), "hips": hips_part(), "torso": torso_part(), "head": head_part(), "mouth-talk": talk_mouth()}
    for kind in ("open", "shut", "happy", "hurt", "dead"):
        out[f"eye-{kind}"] = eyes(kind)
    for side in ("far", "near"):
        out[f"{side}-arm-upper"], out[f"{side}-arm-lower"], out[f"{side}-hand"] = arm_parts(side)
        out[f"{side}-leg"], out[f"{side}-shin"], out[f"{side}-foot"] = leg_parts(side)
    return out


def svg_text() -> str:
    parts = drawn()
    svg.PARTS.clear()
    for group, label, name, bone, z, channel in LAYERS:
        extra = f' data-rig-opacity="{channel}"' + (' data-rig-default="1"' if channel == "eye_open" else "") if channel else ""
        part(group, label, name, bone, z, parts[group], extra)
    return svg.document(
        size=(W, H), design="pulse-voyager-captain-v2", layer_id="pulse-voyager-captain", label=VIEW,
        comment=["  <!-- Captain Pulse: Claude's redesign of the v2 robot, in the Pulse Voyagers' colours, side",
                 "       view facing right; the ground is y=470. Each part is a layer the rig turns about its",
                 "       joint (scripts/svg_art/pulse_voyager_captain_art.py JOINTS). -->"],
        joints=svg.joints_layer({k: (v[1], v[2]) for k, v in JOINTS.items()}),
    )


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".svg.tmp")
    tmp.write_text(svg_text(), encoding="utf8")
    tmp.replace(OUT)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
