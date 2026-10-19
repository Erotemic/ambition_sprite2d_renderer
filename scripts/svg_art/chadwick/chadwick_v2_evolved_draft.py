"""KEPT, NOT CAST: Chadwick as the v2 robot template, evolved (svgkit, Bob's joints).

Drawn 2026-10-18 to show how the v2 robot's design (box head, visor, antenna,
chest panel, beaded limbs) could grow up: kept by Jon, not chosen (Chadwick is
look A of ``chadwick_robot_drafts.py``). No target, config, catalog row or
rig names it; nothing renders it but this script.

    uv run python scripts/svg_art/chadwick/chadwick_v2_evolved_draft.py OUT_DIR [BEFORE.png]
"""
from __future__ import annotations

import io
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import svgkit as svg  # noqa: E402
from svgkit import capsule, clipped, ellipse, line, part, path, smooth  # noqa: E402

W, H = 720, 640
DX, DY = 84.0, 98.0
INK = "#171a1f"
OW = 1.6

J = dict(
    pelvis=(252.0, 300.0), neck=(258.0, 186.0), head_top=(262.0, 96.0),
    near_shoulder=(268.0, 204.0), near_elbow=(286.0, 258.0), near_wrist=(326.0, 250.0),
    far_shoulder=(244.0, 200.0), far_elbow=(236.0, 258.0), far_wrist=(246.0, 308.0),
    near_hip=(260.0, 310.0), near_knee=(272.0, 388.0), near_ankle=(268.0, 452.0),
    far_hip=(244.0, 306.0), far_knee=(246.0, 386.0), far_ankle=(228.0, 452.0),
)

C = dict(
    shell="#f3f4f6", shell_lt="#ffffff", shell_sh="#c9ced6", shell_dk="#a7aeb8",
    far="#d5d9df", far_sh="#b0b6bf",
    suit="#2b3037", suit_lt="#454c56", suit_dk="#1c2025",
    muzzle="#e3e7ec",
    glass="#10151a", glass_lt="#2c3640", glare="#6f8796",
    neon="#7cf05a", neon_dk="#3f9a2c", neon_lt="#d4ffc4",
    badge="#f7f7f2", steel="#8b929c", steel_lt="#c3c8cf",
)


def outlined(sil, fill, items=(), cid=None, width=None):
    body = [path(sil, fill)]
    if items:
        body = clipped(cid, sil, [path(sil, fill)] + list(items))
    return body + [path(sil, "none", INK, width or 2 * OW)]


def rect(x0, y0, x1, y1):
    return smooth([(x0, y0, True), (x1, y0, True), (x1, y1, True), (x0, y1, True)])


def rrect(x0, y0, x1, y1, r):
    """A rounded rectangle as a closed spline (corners eased by ``r``)."""
    return smooth([(x0 + r, y0), (x1 - r, y0), (x1, y0 + r), (x1, y1 - r), (x1 - r, y1), (x0 + r, y1), (x0, y1 - r), (x0, y0 + r)])


def shade_band(sil_pts, d, color):
    """The silhouette moved by ``d``: drawn under a clip, its uncovered rim
    reads as a shade band (painted before the fill copy that covers it)."""
    return path(smooth([(q[0] + d[0], q[1] + d[1]) + tuple(q[2:]) for q in sil_pts]), color)


# --- head: v2's rounded box, visor and antenna, built with depth ---------------------------------
HEAD = [(226, 112), (234, 100), (252, 94), (292, 94), (306, 102), (312, 116), (312, 156), (306, 170), (292, 178),
        (246, 178), (232, 172), (224, 158), (222, 128)]


def head():
    sil = smooth(HEAD)
    items = [path(sil, C["shell_sh"]),
             path(smooth([(q[0] - 4, q[1] - 5) for q in HEAD]), C["shell"]),
             path(smooth([(234, 112), (246, 100), (276, 98), (262, 106), (244, 116), (236, 130)]), C["shell_lt"]),
             # v2's light muzzle patch, as a face plate under the visor
             path(smooth([(262, 150), (308, 148), (310, 166), (300, 176), (268, 176), (258, 166)]), C["muzzle"]),
             line([(258, 150), (262, 176)], C["shell_dk"], 1.2),
             # the seam where the face plate meets the skull
             line([(254, 100), (250, 128), (252, 160), (258, 178)], C["shell_dk"], 1.4)]
    body = outlined(sil, C["shell"], items, "clip-head")
    # the visor: dark glass with a glare, eyes half-lidded (smug)
    vis = rrect(262, 110, 314, 150, 12)
    eyes = []
    for (x, rx) in ((280, 5.0), (300, 4.4)):
        eyes.append(ellipse(x, 131, rx, 8.0, C["neon"]))
        eyes.append(ellipse(x - 1.2, 128, rx * 0.35, 2.6, C["neon_lt"]))
    eyes.append(path(rect(266, 112, 316, 126), C["glass"]))           # the lids, level and lazy
    eyes.append(line([(272, 126), (306, 126)], C["neon_dk"], 1.2))
    glare = [line([(268, 144), (276, 116)], C["glare"], 2.4), line([(274, 146), (280, 132)], C["glass_lt"], 1.6)]
    body += outlined(vis, C["glass"], eyes + glare, "clip-visor")
    # the ear module the antenna rises from, and a status light
    body.append(ellipse(240, 136, 11.0, 13.0, C["shell"], INK, 2 * OW))
    body.append(ellipse(240, 136, 6.5, 8.0, C["suit"], INK, 1.2))
    body.append(ellipse(240, 136, 2.6, 3.2, C["neon"]))
    body.append(path(rrect(246, 84, 254, 96, 2), C["suit"], INK, 1.4))
    body.append(line([(250, 86), (246, 62)], INK, 4.4))
    body.append(line([(250, 86), (246, 62)], C["steel_lt"], 2.0))
    body.append(ellipse(245.5, 58, 6.0, 6.0, C["neon"], INK, 1.6))
    body.append(ellipse(244, 56.5, 2.0, 2.0, C["neon_lt"]))
    part("head", "Head", "head", "head", 60, body)


# --- torso: v2's square chest, tapered, its panel a screen; a dark waist ---------------------------
CHEST = [(232, 200), (240, 190), (262, 186), (282, 190), (294, 202), (296, 228), (290, 256), (278, 272), (242, 274),
         (232, 262), (228, 232)]
PELVIS = [(234, 288), (282, 286), (288, 300), (284, 318), (238, 320), (230, 304)]


def torso():
    body = [path(capsule((256, 176), (258, 196), 9.0, 10.0), C["suit"], INK, 2 * OW),
            line([(250, 182), (264, 182)], C["suit_lt"], 1.4), line([(250, 189), (264, 189)], C["suit_lt"], 1.4)]
    # the waist: a dark flexible core between the chest and the pelvis plate
    body.append(path(capsule((256, 266), (258, 296), 22.0, 22.0), C["suit"], INK, 2 * OW))
    for y in (276, 284):
        body.append(line([(240, y), (276, y)], C["suit_lt"], 1.4))
    sil = smooth(CHEST)
    items = [path(sil, C["shell_sh"]), path(smooth([(q[0] - 4, q[1] - 5) for q in CHEST]), C["shell"]),
             path(smooth([(236, 204), (252, 194), (272, 192), (252, 204), (240, 222)]), C["shell_lt"]),
             line([(246, 248), (290, 246)], C["shell_dk"], 1.2)]
    body += outlined(sil, C["shell"], items, "clip-chest")
    # the chest panel, now a screen: a graph, up and to the right
    body += outlined(rrect(252, 208, 288, 238, 6), C["glass"],
                     [path(rect(252, 230, 288, 238), C["glass_lt"]),
                      line([(256, 230), (264, 222), (270, 226), (278, 214), (284, 212)], C["neon"], 2.4),
                      path(smooth([(279, 209, True), (286, 210, True), (282, 216, True)]), C["neon"])], "clip-screen", 1.6 * 1.4)
    # v2's cable from the panel to a box, as a power bank clipped to the belt
    body.append(line([(262, 238), (266, 254), (276, 270), (282, 292)], INK, 4.6))
    body.append(line([(262, 238), (266, 254), (276, 270), (282, 292)], C["neon_dk"], 2.4))
    psil = smooth(PELVIS)
    body += outlined(psil, C["shell"], [path(smooth([(q[0] + 3, q[1] + 5) for q in PELVIS]), C["shell"]),
                                         path(smooth([(236, 306), (288, 304), (286, 322), (236, 322)]), C["shell_sh"])], "clip-pelvis")
    body += outlined(rrect(274, 288, 298, 312, 4), C["steel"],
                     [path(rect(278, 300, 294, 306), C["suit_dk"]), path(rect(279, 301, 288, 305), C["neon"])], "clip-pack", 2.2)
    # the lanyard: two straps from behind the neck to a badge over the chest
    body.append(line([(252, 190), (254, 214), (262, 244)], C["neon"], 3.0))
    body.append(line([(266, 190), (268, 214), (264, 244)], C["neon_dk"], 3.0))
    body += outlined(rrect(250, 242, 274, 270, 3), C["badge"],
                     [path(rect(254, 246, 270, 256), "#9fd8ff"), line([(255, 262), (269, 262)], "#8d939b", 1.2),
                      line([(255, 266), (264, 266)], "#8d939b", 1.2)], "clip-badge", 2.4)
    part("torso", "Torso", "torso", "torso", 50, body)


def shell_segment(a, b, r0, r1, near, cid):
    """A limb's shell over the dark suit: lit on top, shaded under."""
    fill = C["shell"] if near else C["far"]
    sh = C["shell_sh"] if near else C["far_sh"]
    ux, uy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(ux, uy)
    nx, ny = -uy / d, ux / d
    s = 1 if ny > 0 else -1
    items = [line([(a[0] + nx * r0 * 0.6 * s, a[1] + ny * r0 * 0.6 * s), (b[0] + nx * r1 * 0.6 * s, b[1] + ny * r1 * 0.6 * s)], sh, 5.0),
             line([(a[0] - nx * r0 * 0.45 * s, a[1] - ny * r0 * 0.45 * s), (b[0] - nx * r1 * 0.45 * s, b[1] - ny * r1 * 0.45 * s)],
                  C["shell_lt"] if near else C["shell"], 2.4)]
    return outlined(capsule(a, b, r0, r1), fill, items, cid)


def joint(c, r, near):
    return [ellipse(c[0], c[1], r, r, C["suit"] if near else C["suit_dk"], INK, 2 * OW),
            ellipse(c[0] - r * 0.25, c[1] - r * 0.25, r * 0.45, r * 0.45, C["suit_lt"])]


def leg(side):
    near = side == "near"
    zb = 30 if near else 20
    hip, knee, ankle = J[f"{side}_hip"], J[f"{side}_knee"], J[f"{side}_ankle"]
    # the dark suit runs the whole leg; shells sit on the thigh and shin
    suit = path(capsule(hip, ankle if False else knee, 11.0, 9.0), C["suit"] if near else C["suit_dk"], INK, 2 * OW)
    th = (hip[0] + (knee[0] - hip[0]) * 0.12, hip[1] + (knee[1] - hip[1]) * 0.12)
    tk = (hip[0] + (knee[0] - hip[0]) * 0.80, hip[1] + (knee[1] - hip[1]) * 0.80)
    part(f"{side}-thigh", "", f"{side}_leg_u", f"{side}_leg_u", zb + 2, [suit] + shell_segment(th, tk, 15.0, 13.0, near, f"c-{side}-th"))
    sk = (knee[0] + (ankle[0] - knee[0]) * 0.22, knee[1] + (ankle[1] - knee[1]) * 0.22)
    sa = (knee[0] + (ankle[0] - knee[0]) * 0.86, knee[1] + (ankle[1] - knee[1]) * 0.86)
    body = [path(capsule(knee, ankle, 9.0, 8.0), C["suit"] if near else C["suit_dk"], INK, 2 * OW)]
    body += shell_segment(sk, sa, 13.0, 11.0, near, f"c-{side}-sh")
    body += joint(knee, 10.0, near)
    # a white knee cap over the joint
    body += outlined(smooth([(knee[0] + 2, knee[1] - 12), (knee[0] + 14, knee[1] - 6), (knee[0] + 14, knee[1] + 8), (knee[0] + 4, knee[1] + 10)]),
                     C["shell"] if near else C["far"], [], None)
    part(f"{side}-shin", "", f"{side}_leg_l", f"{side}_leg_l", zb + 1, body)
    ax, ay = ankle
    boot = smooth([(ax - 16, ay - 14), (ax + 8, ay - 16), (ax + 20, ay - 8), (ax + 38, ay - 2), (ax + 46, ay + 8),
                   (ax + 46, ay + 18, True), (ax - 18, ay + 18, True), (ax - 19, ay + 2)])
    items = [path(rect(ax - 22, ay + 10, ax + 50, ay + 20), C["suit_dk"]),
             path(rect(ax - 22, ay + 7, ax + 50, ay + 11), C["neon"] if near else C["neon_dk"]),
             path(smooth([(ax - 14, ay - 12), (ax + 6, ay - 14), (ax + 2, ay - 2), (ax - 14, ay)]), C["shell_lt"] if near else C["far"]),
             line([(ax + 18, ay - 6), (ax + 30, ay + 0)], C["shell_sh"], 1.6)]
    part(f"{side}-foot", "", f"{side}_foot", f"{side}_foot", zb + 3, outlined(boot, C["shell"] if near else C["far"], items, f"c-{side}-boot"))


def arm(side):
    near = side == "near"
    zb = 80 if near else 10
    sh, el, wr = J[f"{side}_shoulder"], J[f"{side}_elbow"], J[f"{side}_wrist"]
    body = [path(capsule(sh, el, 8.5, 7.5), C["suit"] if near else C["suit_dk"], INK, 2 * OW)]
    a = (sh[0] + (el[0] - sh[0]) * 0.25, sh[1] + (el[1] - sh[1]) * 0.25)
    b = (sh[0] + (el[0] - sh[0]) * 0.82, sh[1] + (el[1] - sh[1]) * 0.82)
    body += shell_segment(a, b, 11.0, 10.0, near, f"c-{side}-ua")
    # the shoulder cap: a rounded dome over the joint
    body += outlined(smooth([(sh[0] - 15, sh[1] + 4), (sh[0] - 12, sh[1] - 10), (sh[0], sh[1] - 15), (sh[0] + 13, sh[1] - 10),
                             (sh[0] + 16, sh[1] + 4), (sh[0], sh[1] + 9)]), C["shell"] if near else C["far"],
                     [path(smooth([(sh[0] - 15, sh[1] + 4), (sh[0] + 16, sh[1] + 4), (sh[0] + 16, sh[1] + 12), (sh[0] - 15, sh[1] + 12)]),
                           C["shell_sh"] if near else C["far_sh"])], f"c-{side}-cap")
    part(f"{side}-arm-u", "", f"{side}_arm_u", f"{side}_arm_u", zb, body)
    body = [path(capsule(el, wr, 7.5, 6.5), C["suit"] if near else C["suit_dk"], INK, 2 * OW)]
    a = (el[0] + (wr[0] - el[0]) * 0.25, el[1] + (wr[1] - el[1]) * 0.25)
    b = (el[0] + (wr[0] - el[0]) * 0.92, el[1] + (wr[1] - el[1]) * 0.92)
    body += shell_segment(a, b, 9.5, 11.5, near, f"c-{side}-fa")   # a gauntlet, wider at the wrist
    body += joint(el, 8.5, near)
    part(f"{side}-arm-l", "", f"{side}_arm_l", f"{side}_arm_l", zb - 2, body)
    wx, wy = wr
    fill = C["shell"] if near else C["far"]
    hand = smooth([(wx - 2, wy - 9), (wx + 12, wy - 11), (wx + 20, wy - 6), (wx + 21, wy + 5), (wx + 12, wy + 11), (wx - 2, wy + 9)])
    hb = outlined(hand, fill, [line([(wx + 10, wy - 10), (wx + 11, wy + 10)], C["suit"], 1.6),
                               line([(wx + 15, wy - 8), (wx + 16, wy + 8)], C["suit"], 1.4),
                               path(smooth([(wx - 2, wy + 2), (wx + 20, wy + 2), (wx + 21, wy + 12), (wx - 2, wy + 12)]), C["shell_sh"])], f"c-{side}-hand")
    if near:
        # v2's tablet, held up and showing the pitch
        tab = [path(rrect(wx + 4, wy - 50, wx + 34, wy + 6, 4), C["suit_dk"], INK, 2 * OW),
               path(rrect(wx + 7, wy - 47, wx + 31, wy + 3, 2), C["glass"]),
               line([(wx + 10, wy - 6), (wx + 15, wy - 16), (wx + 20, wy - 12), (wx + 28, wy - 36)], C["neon"], 2.2),
               path(smooth([(wx + 24, wy - 40, True), (wx + 31, wy - 39, True), (wx + 27, wy - 33, True)]), C["neon"]),
               line([(wx + 10, wy - 42), (wx + 20, wy - 42)], C["glass_lt"], 2.0)]
        hb = tab + hb
    part(f"{side}-hand", "", f"{side}_hand", f"{side}_hand", zb + 4, hb)


def draw():
    svg.configure(dx=DX, dy=DY, ink=INK, ow=OW, colors=C)
    arm("far")
    leg("far")
    leg("near")
    torso()
    head()
    arm("near")
    return svg.document(size=(W, H), design="chadwick-evolved", layer_id="chadwick", label="Chadwick",
                        comment=["  <!-- KEPT, NOT CAST: the v2 robot template evolved (2026-10-18), not registered in the cast.",
                                 "       Drawn by scripts/svg_art/chadwick/chadwick_v2_evolved_draft.py. -->"],
                        joints=svg.joints_layer(J))


if __name__ == "__main__":
    import resvg_py
    from PIL import Image, ImageDraw
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    text = draw()
    (out / "chadwick_evolved.svg").write_text(text)
    png = bytes(resvg_py.svg_to_bytes(svg_string=text.replace("720mm", "720").replace("640mm", "640")))
    im = Image.open(io.BytesIO(png)).convert("RGBA").crop((200, 120, 640, 640))
    before = Image.open(sys.argv[2]).convert("RGBA") if len(sys.argv) > 2 else None
    sheet = Image.new("RGBA", (880, 520), (96, 104, 112, 255))
    if before is not None:
        bh = 420
        b = before.resize((int(before.width * bh / before.height), bh), Image.LANCZOS)
        sheet.alpha_composite(b, ((440 - b.width) // 2, 520 - bh - 40))
    sheet.alpha_composite(im, (440, 0))
    d = ImageDraw.Draw(sheet)
    d.text((8, 8), "Chadwick today (the v2 robot template)", fill=(255, 255, 0, 255))
    d.text((448, 8), "Chadwick, evolved", fill=(255, 255, 0, 255))
    sheet.save(out / "chadwick_evolved_vs_v2.png")
    im.save(out / "chadwick_evolved.png")
    print(out / "chadwick_evolved_vs_v2.png")
