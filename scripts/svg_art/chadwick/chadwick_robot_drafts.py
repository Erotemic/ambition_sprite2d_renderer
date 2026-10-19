"""Chadwick Disruptor III, a robot tech bro: three drafts on Bob's joints (svgkit).

Jon chose look A, the founder-bot (2026-10-18): Chadwick's design. B (a
phone for a head, in a hoodie) and C (a VR-headset visionary in a
quarter-zip) are KEPT, NOT CAST: no target, config, catalog row or rig names
them. Until Chadwick's rig is built, nothing renders any of these but this
script; his sheet is still the robot template's.

    uv run python scripts/svg_art/chadwick/chadwick_robot_drafts.py OUT_DIR
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import svgkit as svg  # noqa: E402
from svgkit import capsule, clipped, ellipse, line, part, path, smooth  # noqa: E402

W, H = 720, 640
DX, DY = 84.0, 98.0
INK = "#121417"
OW = 1.6

J = dict(
    pelvis=(250.0, 302.0), neck=(258.0, 182.0), head_top=(266.0, 108.0),
    near_shoulder=(266.0, 196.0), near_elbow=(282.0, 252.0), near_wrist=(322.0, 246.0),
    far_shoulder=(246.0, 192.0), far_elbow=(238.0, 254.0), far_wrist=(250.0, 304.0),
    near_hip=(258.0, 304.0), near_knee=(270.0, 384.0), near_ankle=(266.0, 456.0),
    far_hip=(242.0, 300.0), far_knee=(244.0, 382.0), far_ankle=(226.0, 456.0),
)

NEON, NEON_DARK, NEON_GLOW = "#7cf05a", "#3f9a2c", "#d9ffc9"
SCREEN, SCREEN_EDGE = "#0f1418", "#2b333b"

LOOKS = {
    "founder": dict(label="A: founder-bot (white gadget, fleece vest)",
                    shell="#f1f2f4", shell_sh="#c3c8cf", shell_lt="#ffffff", joint="#3a4048", joint_lt="#5a626c",
                    far="#d6dae0", head="visor", top="vest", vest="#4b5058", vest_sh="#33373e", vest_lt="#646a73",
                    feet="sneaker", lanyard=True, prop="phone"),
    "phonehead": dict(label="B: phone-head (screen for a face, hoodie)",
                      shell="#c9ced6", shell_sh="#959ca6", shell_lt="#e8ebef", joint="#2d3238", joint_lt="#4a515a",
                      far="#aab0b9", head="phone", top="hoodie", hoodie="#6fd64e", hoodie_sh="#4aa531", hoodie_lt="#97ea78",
                      feet="chunky", chain=True, prop="tablet"),
    "visionary": dict(label="C: VR visionary (headset face, quarter-zip)",
                      shell="#2a2f36", shell_sh="#1a1d22", shell_lt="#434a54", joint="#7cf05a", joint_lt="#b6ff9c",
                      far="#20242a", head="headset", top="zip", zip="#e9ecef", zip_sh="#bfc5cc", zip_lt="#ffffff",
                      feet="robot", lanyard=True, prop="coffee"),
}


def outlined(sil, fill, items=(), cid=None, width=None):
    body = [path(sil, fill)]
    if items:
        body = clipped(cid, sil, [path(sil, fill)] + list(items))
    return body + [path(sil, "none", INK, width or 2 * OW)]


def rect(x0, y0, x1, y1):
    return smooth([(x0, y0, True), (x1, y0, True), (x1, y1, True), (x0, y1, True)])


def screen_face(o, cx, cy, w, h, cid):
    """Neon pixel eyes, half-lidded (smug), and a lopsided pixel smirk."""
    items = [path(rect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), SCREEN)]
    ex = (cx + w * 0.02, cx + w * 0.30)
    for x in ex:
        items.append(path(rect(x - 4.5, cy - h * 0.18, x + 4.5, cy + h * 0.02), NEON))
        items.append(path(rect(x - 5.5, cy - h * 0.24, x + 5.5, cy - h * 0.10), SCREEN))  # the lazy lid
    items.append(path(smooth([(cx - w * 0.02, cy + h * 0.22, True), (cx + w * 0.30, cy + h * 0.22, True),
                              (cx + w * 0.38, cy + h * 0.12, True), (cx + w * 0.38, cy + h * 0.17, True),
                              (cx + w * 0.32, cy + h * 0.28, True), (cx - w * 0.02, cy + h * 0.28, True)]), NEON))
    items.append(line([(cx - w / 2 + 3, cy - h / 2 + 4), (cx - w / 2 + 12, cy - h / 2 + 4)], "#3a4652", 2.0))
    return items


def head(o):
    shell, sh, lt = o["shell"], o["shell_sh"], o["shell_lt"]
    body = []
    if o["head"] == "visor":
        skull = smooth([(234, 150), (232, 122), (240, 106), (258, 98), (282, 98), (300, 108), (306, 124), (306, 152),
                        (300, 168), (282, 176), (256, 176), (240, 168)])
        items = [path(smooth([(236, 156), (300, 160), (302, 180), (236, 180)]), sh),
                 path(smooth([(246, 104), (272, 100), (262, 110), (244, 116)]), lt)]
        body += outlined(skull, shell, items, "clip-skull")
        visor = smooth([(266, 116), (300, 114), (308, 124), (308, 150), (300, 160), (268, 160), (262, 146), (262, 126)])
        body += outlined(visor, SCREEN, screen_face(o, 287, 137, 38, 40, "f"), "clip-visor")
        # an earbud for an ear, and a stub antenna
        body.append(ellipse(250, 138, 8.0, 10.0, "#ffffff", INK, 1.6))
        body.append(ellipse(250, 138, 3.0, 4.0, "#d3d7dc"))
        body.append(line([(258, 98), (254, 82)], INK, 3.0))
        body.append(ellipse(254, 80, 4.0, 4.0, NEON, INK, 1.4))
    elif o["head"] == "phone":
        phone = smooth([(246, 92, True), (300, 92, True), (304, 96), (304, 172), (300, 176, True), (246, 176, True),
                        (242, 172), (242, 96)])
        body += outlined(phone, "#1b1f24", [], "clip-phone")
        body += outlined(rect(248, 100, 298, 168), SCREEN, screen_face(o, 276, 136, 48, 64, "f") + [
            path(rect(266, 100, 286, 106), "#1b1f24")], "clip-screen")
        body.append(line([(304, 118), (304, 132)], "#5a626c", 2.4))
        body.append(path(rect(240, 172, 276, 182), o["joint"], INK, 1.4))  # the neck mount
    else:  # headset
        skull = smooth([(236, 152), (234, 124), (244, 106), (262, 98), (284, 100), (298, 112), (300, 130), (298, 160),
                        (286, 174), (258, 176), (242, 168)])
        body += outlined(skull, shell, [path(smooth([(240, 158), (296, 162), (296, 180), (240, 180)]), o["shell_sh"])], "clip-skull")
        strap = [line([(238, 120), (262, 112), (290, 112)], "#101214", 6.0)]
        body += strap
        hs = smooth([(268, 108, True), (310, 106), (318, 116), (318, 142), (310, 152), (268, 152, True), (262, 130)])
        body += outlined(hs, "#16191d", [path(smooth([(272, 138, True), (316, 136, True), (316, 142, True), (272, 144, True)]), NEON),
                                         line([(276, 116), (306, 114)], "#3a414a", 2.4)], "clip-hs")
        body.append(ellipse(300, 160, 6.0, 4.0, NEON_GLOW))  # a smug glow under it
        body.append(line([(286, 162), (296, 164), (306, 158)], NEON, 2.4))
    part("head", "Head", "head", "head", 60, body)


TORSO = [(236, 194), (250, 184), (270, 184), (284, 194), (292, 214), (293, 246), (289, 276), (283, 304),
         (230, 304), (224, 274), (225, 236), (229, 208)]


def torso(o):
    sil = smooth(TORSO)
    shell, sh, lt = o["shell"], o["shell_sh"], o["shell_lt"]
    items = [path(smooth([(276, 196), (291, 212), (292, 250), (284, 250), (280, 214)]), lt),
             path(smooth([(225, 236), (236, 238), (238, 300), (225, 300)]), sh),
             path(rect(240, 222, 270, 250), SCREEN_EDGE), path(rect(243, 225, 267, 247), SCREEN),
             line([(246, 236), (252, 232), (258, 240), (264, 228)], NEON, 2.0)]  # a chest display: a graph going up
    if o["top"] == "vest":
        front = smooth([(266, 196), (282, 200), (291, 218), (293, 248), (289, 278), (283, 304), (262, 304), (266, 262), (268, 226)])
        back = smooth([(238, 196), (252, 192), (256, 230), (252, 270), (250, 304), (228, 304), (224, 270), (226, 232), (230, 208)])
        items += [path(back, o["vest"], INK, 1.6), path(front, o["vest"], INK, 1.6),
                  path(smooth([(224, 236), (234, 238), (236, 300), (224, 300)]), o["vest_sh"]),
                  path(smooth([(280, 220), (291, 222), (291, 276), (282, 296)]), o["vest_lt"])]
        for y in (220, 240, 260, 280):
            items += [line([(228, y), (252, y + 2)], o["vest_sh"], 1.3), line([(268, y + 2), (290, y)], o["vest_sh"], 1.3)]
        items += [line([(266, 200), (264, 300)], "#9aa0a8", 1.4), path(rect(274, 211, 282, 217), NEON)]
    elif o["top"] == "hoodie":
        items = [path(sil, o["hoodie"]),
                 path(smooth([(276, 196), (291, 212), (292, 250), (284, 250), (280, 214)]), o["hoodie_lt"]),
                 path(smooth([(225, 236), (236, 238), (238, 300), (225, 300)]), o["hoodie_sh"]),
                 path(smooth([(258, 252), (290, 250), (291, 284), (262, 286)]), o["hoodie_sh"], INK, 1.4),
                 path(rect(272, 208, 286, 222), "#1d2b18"), line([(276, 210), (282, 220)], NEON, 1.6),
                 line([(282, 210), (276, 220)], NEON, 1.6),
                 path(rect(222, 290, 292, 306), o["hoodie_sh"])]
    else:  # quarter zip, white over the dark chassis
        items = [path(sil, o["zip"]), path(smooth([(276, 196), (291, 212), (292, 250), (284, 250), (280, 214)]), o["zip_lt"]),
                 path(smooth([(225, 236), (236, 238), (238, 300), (225, 300)]), o["zip_sh"]),
                 path(smooth([(252, 182, True), (272, 184, True), (276, 202), (262, 204), (254, 198)]), o["zip_sh"], INK, 1.4),
                 line([(268, 186), (270, 226)], "#8a9098", 1.6), path(rect(268, 224, 274, 234), NEON),
                 path(rect(278, 213, 286, 219), NEON)]
    body = [path(capsule((258, 176), (260, 196), 10.0, 11.0), o["joint"], INK, 2 * OW)]
    if o["top"] == "hoodie":
        body.append(path(smooth([(226, 182), (240, 170), (258, 176), (262, 196), (240, 204), (226, 198)]), o["hoodie"], INK, 2 * OW))
    body += outlined(sil, shell, items, "clip-torso")
    if o.get("lanyard"):
        body += [line([(256, 188), (262, 222), (270, 248)], NEON, 3.0), line([(270, 190), (272, 222), (270, 248)], NEON_DARK, 3.0),
                 path(rect(260, 246, 280, 272), "#f4f4f0", INK, 1.4), path(rect(263, 250, 277, 260), "#9fd8ff"),
                 line([(264, 265), (276, 265)], "#888", 1.2)]
    if o.get("chain"):
        body += [line([(252, 188), (258, 212), (270, 224), (280, 210), (278, 192)], "#e3b23c", 2.6),
                 path(smooth([(266, 222), (274, 222), (274, 232), (270, 236), (266, 232)]), "#e3b23c", INK, 1.0)]
    part("torso", "Torso", "torso", "torso", 50, body)


def hips(o):
    sil = smooth([(228, 292, True), (284, 292, True), (288, 312), (282, 330), (232, 332), (226, 314)])
    part("hips", "Hips", "hips", "pelvis", 48, outlined(sil, o["joint"], [line([(232, 300), (284, 300)], o["joint_lt"], 2.0)], "clip-hips"))


def limb(o, a, b, r0, r1, fill, sh, cid, z, name, bone):
    sil = capsule(a, b, r0, r1)
    part(cid, "", name, bone, z, outlined(sil, fill, [line([(a[0] + r0 * 0.4, a[1] + 2), (b[0] + r1 * 0.4, b[1] - 2)], sh, 2.4)], "clip-" + cid))


def joint_ring(o, c, r, z, name, bone):
    part(f"ring-{name}", "", f"{name}_ring", bone, z, [ellipse(c[0], c[1], r, r, o["joint"], INK, 1.6),
                                                        ellipse(c[0] - r * 0.3, c[1] - r * 0.3, r * 0.35, r * 0.35, o["joint_lt"])])


def leg(o, side):
    near = side == "near"
    zb = 30 if near else 20
    fill = o["shell"] if near else o["far"]
    hip, knee, ankle = J[f"{side}_hip"], J[f"{side}_knee"], J[f"{side}_ankle"]
    limb(o, hip, knee, 15.0, 13.0, fill, o["shell_sh"], f"{side}-thigh", zb + 2, f"{side}_leg_u", f"{side}_leg_u")
    limb(o, knee, ankle, 13.0, 11.0, fill, o["shell_sh"], f"{side}-shin", zb + 1, f"{side}_leg_l", f"{side}_leg_l")
    joint_ring(o, knee, 11.0, zb + 3, f"{side}_knee", f"{side}_leg_l")
    ax, ay = ankle
    if o["feet"] == "robot":
        foot = smooth([(ax - 14, ay - 8), (ax + 12, ay - 10), (ax + 36, ay + 2), (ax + 40, ay + 18, True), (ax - 16, ay + 18, True)])
        part(f"{side}-foot", "", f"{side}_foot", f"{side}_foot", zb + 4,
             outlined(foot, fill, [path(rect(ax - 20, ay + 12, ax + 44, ay + 20), NEON)], f"clip-{side}-foot"))
    else:
        tall = 9 if o["feet"] == "chunky" else 6
        shoe = smooth([(ax - 15, ay - 12), (ax + 8, ay - 14), (ax + 22, ay - 5), (ax + 38, ay + 1), (ax + 43, ay + 10),
                       (ax + 43, ay + 18, True), (ax - 17, ay + 18, True), (ax - 18, ay + 3)])
        white = "#f6f7f9" if near else "#c9ced6"
        part(f"{side}-foot", "", f"{side}_foot", f"{side}_foot", zb + 4,
             outlined(shoe, white, [path(rect(ax - 20, ay + 18 - tall, ax + 46, ay + 20), NEON if o["feet"] == "sneaker" else "#f6f7f9"),
                                    path(smooth([(ax + 6, ay + 2), (ax + 22, ay - 2), (ax + 26, ay + 6), (ax + 10, ay + 8)]), NEON)],
                      f"clip-{side}-shoe"))


def arm(o, side):
    near = side == "near"
    zb = 80 if near else 10
    fill = o["shell"] if near else o["far"]
    sh, el, wr = J[f"{side}_shoulder"], J[f"{side}_elbow"], J[f"{side}_wrist"]
    sleeve = {"hoodie": ("hoodie", "hoodie_sh"), "zip": ("zip", "zip_sh")}.get(o["top"])
    if sleeve:
        sf = o[sleeve[0]] if near else o[sleeve[1]]
        limb(o, sh, el, 15.0, 12.5, sf, o[sleeve[1]], f"{side}-arm-u", zb, f"{side}_arm_u", f"{side}_arm_u")
    else:
        limb(o, sh, el, 12.0, 10.5, fill, o["shell_sh"], f"{side}-arm-u", zb, f"{side}_arm_u", f"{side}_arm_u")
        joint_ring(o, sh, 12.0, zb + 1, f"{side}_shoulder", f"{side}_arm_u")
    limb(o, el, wr, 10.5, 9.0, fill, o["shell_sh"], f"{side}-arm-l", zb - 2, f"{side}_arm_l", f"{side}_arm_l")
    joint_ring(o, el, 9.0, zb - 1, f"{side}_elbow", f"{side}_arm_l")
    wx, wy = wr
    hand = smooth([(wx - 4, wy - 9), (wx + 12, wy - 10), (wx + 18, wy - 4), (wx + 18, wy + 6), (wx + 10, wy + 10), (wx - 4, wy + 8)])
    body = outlined(hand, fill, [line([(wx + 8, wy - 9), (wx + 9, wy + 9)], o["shell_sh"], 1.4)], f"clip-{side}-hand")
    prop = o["prop"]
    if near and prop == "phone":
        body = [path(rect(wx + 6, wy - 32, wx + 22, wy + 2), "#111418", INK, 2.0), path(rect(wx + 8, wy - 29, wx + 20, wy - 2), SCREEN),
                line([(wx + 10, wy - 12), (wx + 13, wy - 18), (wx + 16, wy - 14), (wx + 19, wy - 26)], NEON, 1.6)] + body
    elif near and prop == "tablet":
        body = [path(rect(wx + 4, wy - 40, wx + 30, wy + 4), "#111418", INK, 2.0), path(rect(wx + 7, wy - 37, wx + 27, wy + 1), SCREEN),
                line([(wx + 9, wy - 8), (wx + 14, wy - 16), (wx + 19, wy - 12), (wx + 25, wy - 30)], NEON, 1.8)] + body
    elif near and prop == "coffee":
        body = [path(smooth([(wx + 2, wy - 30, True), (wx + 24, wy - 30, True), (wx + 21, wy + 6, True), (wx + 5, wy + 6, True)]), "#f4efe6", INK, 2.0),
                path(rect(wx + 1, wy - 34, wx + 25, wy - 28), "#2a2f36"), path(rect(wx + 4, wy - 16, wx + 22, wy - 8), NEON_DARK)] + body
    part(f"{side}-hand", "", f"{side}_hand", f"{side}_hand", zb + 4, body)


def draw(key):
    o = LOOKS[key]
    svg.configure(dx=DX, dy=DY, ink=INK, ow=OW, colors={})
    arm(o, "far")
    leg(o, "far")
    leg(o, "near")
    torso(o)
    hips(o)
    head(o)
    arm(o, "near")
    note = ("CHADWICK's design (Jon chose look A, 2026-10-18); his rig is not built yet." if key == "founder"
            else "KEPT, NOT CAST: a Chadwick draft Jon did not choose (2026-10-18), not registered in the cast.")
    return svg.document(size=(W, H), design=f"tech-bro-robot-{key}", layer_id="chadwick", label="Chadwick",
                        comment=[f"  <!-- {note}", "       Drawn by scripts/svg_art/chadwick/chadwick_robot_drafts.py. -->"],
                        joints=svg.joints_layer(J))


if __name__ == "__main__":
    import resvg_py
    from PIL import Image, ImageDraw
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    tiles = []
    for key in LOOKS:
        text = draw(key)
        (out / f"chadwick_robot_{key}.svg").write_text(text)  # A is "founder"
        png = bytes(resvg_py.svg_to_bytes(svg_string=text.replace("720mm", "720").replace("640mm", "640")))
        tiles.append((LOOKS[key]["label"], Image.open(io.BytesIO(png)).convert("RGBA")))
    sheet = Image.new("RGBA", (440 * len(tiles), 520), (96, 104, 112, 255))
    d = ImageDraw.Draw(sheet)
    for i, (label, im) in enumerate(tiles):
        sheet.alpha_composite(im.crop((200, 120, 640, 640)), (440 * i, 0))
        d.text((440 * i + 8, 8), label, fill=(255, 255, 0, 255))
    sheet.save(out / "chadwick_robot_candidates.png")
    print(out / "chadwick_robot_candidates.png")
