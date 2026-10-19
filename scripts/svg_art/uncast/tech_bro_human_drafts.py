"""KEPT, NOT CAST: three HUMAN tech-bro drafts. Not registered in the cast.

Drawn 2026-10-18 as candidates for Chadwick Disruptor III, who is a ROBOT, so
none was used (Jon: keep them in case he wants them later, do not register
them). No target, config, catalog row or rig names them; nothing renders them
but this script. On Bob's humanoid joints, with ``svgkit``:
1 fleece-vest founder, 2 hype-hoodie crypto bro, 3 quarter-zip growth hacker.

    uv run python scripts/svg_art/uncast/tech_bro_human_drafts.py OUT_DIR
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import svgkit as svg  # noqa: E402
from svgkit import capsule, clipped, ellipse, line, part, path, smooth  # noqa: E402

W, H = 720, 640
DX, DY = 84.0, 98.0
INK = "#15140f"
OW = 1.6

J = dict(
    pelvis=(250.0, 302.0), neck=(258.0, 182.0), head_top=(266.0, 108.0),
    near_shoulder=(266.0, 196.0), near_elbow=(282.0, 252.0), near_wrist=(322.0, 246.0),
    far_shoulder=(246.0, 192.0), far_elbow=(238.0, 254.0), far_wrist=(250.0, 304.0),
    near_hip=(258.0, 304.0), near_knee=(270.0, 384.0), near_ankle=(266.0, 456.0),
    far_hip=(242.0, 300.0), far_knee=(244.0, 382.0), far_ankle=(226.0, 456.0),
)
HEAD_XF = (258.0, 182.0, 1.04)

BASE = dict(
    skin="#e3b48f", skin_light="#f2cdae", skin_shadow="#b9876a", far_skin="#c99a78",
    eye_white="#f7f2ea", iris="#3a4a5c", mouth="#5a2420", tooth="#f6efe0",
    neon="#7cf05a", neon_dark="#3f9a2c", glass="#1b2128", glass_light="#5b6b7a",
    badge="#f4f4f0", sole_dark="#c9ccd1", white="#f6f7f9", white_shadow="#c9ced6",
    gold="#e3b23c", gold_dark="#a87a1e",
)

OUTFITS = {
    "vest": dict(label="1: fleece-vest founder", hair="swoop", hair_c="#7a5434", hair_light="#9c7148",
                 shirt="#a9cdea", shirt_dark="#7ea6c8", shirt_light="#cfe4f5", top="vest", vest="#4b5058", vest_dark="#33373e",
                 vest_light="#646a73", pants="#c9b388", pants_dark="#a08b63", pants_light="#ddc9a3", shoe="sneaker",
                 sole="#7cf05a", lanyard=True, prop_far="watch"),
    "hoodie": dict(label="2: hype-hoodie crypto bro", hair="fade", hair_c="#2b2320", hair_light="#4c3d36",
                   shirt="#6fd64e", shirt_dark="#4aa531", shirt_light="#97ea78", top="hoodie", pants="#24272c",
                   pants_dark="#16181b", pants_light="#3b4048", shoe="chunky", sole="#f6f7f9", chain=True, goggles=True,
                   prop_far="can"),
    "quarterzip": dict(label="3: quarter-zip growth hacker", hair="bun", hair_c="#b88a4a", hair_light="#d7ab69",
                       shirt="#22262b", shirt_dark="#15181b", shirt_light="#3a4048", top="zip", pants="#7d838b",
                       pants_dark="#5f646b", pants_light="#9aa0a8", shoe="sneaker", sole="#f6f7f9", lanyard=True,
                       prop_far="cup"),
}


def outlined(sil, fill, items=(), cid=None, width=None):
    body = [path(sil, fill)]
    if items:
        body = clipped(cid, sil, [path(sil, fill)] + list(items))
    return body + [path(sil, "none", INK, width or 2 * OW)]


SKULL = [(234, 150), (232, 128), (239, 111), (253, 100), (272, 98), (288, 105), (296, 118), (299, 128, True),
         (309, 141, True), (300, 146), (302, 154), (299, 165), (292, 174), (278, 179), (262, 177), (248, 168), (240, 160)]


def head(o, C):
    svg.transform(HEAD_XF)
    sil = smooth(SKULL)
    items = [path(smooth([(276, 130), (294, 128), (300, 144), (284, 148)]), C["skin_light"]),
             path(smooth([(246, 164), (292, 172), (300, 190), (238, 190)]), C["skin_shadow"]),
             # a strong clean-shaven jaw line
             line([(256, 164), (272, 174), (290, 172)], C["skin_shadow"], 1.6),
             line([(299, 128), (307, 140), (300, 144)], C["skin_shadow"], 1.6),
             ellipse(300, 142, 2.0, 1.2, C["skin_shadow"]),
             ellipse(258, 140, 6.0, 8.5, C["skin"], INK, 1.6),
             line([(257, 135), (260, 141), (257, 146)], C["skin_shadow"], 1.6)]
    body = clipped("clip-head", sil, [path(sil, C["skin"])] + items)
    body.append(path(sil, "none", INK, 2 * OW))
    # an earbud in the ear
    body.append(path(smooth([(258, 140), (263, 139), (264, 145), (260, 152, True), (257, 151), (258, 145)]), C["white"], INK, 1.2))
    hc, hl = o["hair_c"], o["hair_light"]
    if o["hair"] == "swoop":
        # Swept up and back with product, short sides.
        hair = smooth([(236, 140), (233, 122), (238, 106), (250, 95), (266, 88), (284, 86, True), (300, 92), (306, 104, True),
                       (294, 104), (282, 106), (268, 108), (256, 114), (250, 126), (248, 140, True), (240, 146)])
        body.append(path(hair, hc, INK, 2 * OW))
        for pts in ([(250, 98), (268, 92), (292, 92)], [(244, 110), (258, 102), (280, 98)], [(238, 124), (246, 112)]):
            body.append(line(pts, hl, 2.0))
    elif o["hair"] == "fade":
        # A short textured crop on top, faded sides.
        body.append(path(smooth([(236, 146), (233, 124), (240, 108), (254, 98), (274, 96), (290, 101), (298, 110, True),
                                 (282, 110), (264, 112), (252, 122), (248, 140, True)]), "#8b6c5c", None))
        hair = smooth([(244, 112), (250, 100), (262, 92), (280, 90), (294, 96), (300, 108, True), (284, 106), (268, 106),
                       (254, 110), (246, 118, True)])
        body.append(path(hair, hc, INK, 2 * OW))
        for x in (256, 266, 276, 286):
            body.append(line([(x, 96), (x + 4, 104)], hl, 1.6))
    else:
        # Pulled back tight into a bun.
        hair = smooth([(236, 146), (233, 124), (239, 108), (252, 98), (270, 95), (288, 99), (298, 110, True),
                       (284, 110), (268, 109), (254, 114), (248, 126), (246, 142, True), (240, 148)])
        body.append(path(hair, hc, INK, 2 * OW))
        body.append(path(smooth([(222, 112), (230, 100), (242, 102), (244, 114), (236, 120), (224, 120)]), hc, INK, 2 * OW))
        body.append(line([(240, 104), (238, 118)], "#2a2a2a", 3.0))
        for pts in ([(246, 104), (262, 100), (284, 102)], [(240, 120), (250, 110), (266, 106)]):
            body.append(line(pts, hl, 1.8))
    # brow, eye, smirk
    body.append(path(smooth([(282, 121, True), (291, 117), (300, 119, True), (291, 123)]), hc, INK, 1.0))
    x, y = 290.0, 131.0
    body.append(path(smooth([(x - 6, y), (x - 1, y - 3.5), (x + 5, y - 2), (x + 6, y + 1), (x + 1, y + 2.6), (x - 4, y + 2)]),
                     C["eye_white"], INK, 1.2))
    body.append(ellipse(x + 2.2, y - 0.2, 2.4, 2.6, C["iris"]))
    body.append(ellipse(x + 1.5, y - 1.1, 0.7, 0.7, "#ffffff"))
    body.append(line([(x - 6, y - 2.8), (x, y - 4.6), (x + 6, y - 2.4)], INK, 1.6))  # a lazy lid: smug
    mx, my = 296.0, 160.0
    body.append(line([(mx - 9, my + 1), (mx - 2, my + 1.6), (mx + 5, my - 2.5)], INK, 1.8))
    body.append(line([(mx + 4, my - 3.4), (mx + 6, my - 1.2)], INK, 1.2))
    if o.get("goggles"):
        body.append(line([(232, 118), (252, 106), (276, 101), (298, 103)], "#101214", 4.5))
        body.append(path(smooth([(268, 94, True), (300, 94), (306, 102), (304, 112, True), (270, 112, True), (264, 104)]),
                         C["glass"], INK, 1.8))
        body.append(line([(274, 100), (296, 99)], C["glass_light"], 2.0))
        body.append(line([(278, 108), (300, 107)], C["neon"], 1.4))
    svg.transform(None)
    part("head", "Head", "head", "head", 60, body)


TORSO = [(238, 194), (250, 185), (268, 185), (282, 195), (290, 214), (291, 246), (288, 276), (283, 304),
         (230, 304), (225, 274), (226, 236), (229, 208)]


def torso(o, C):
    sil = smooth(TORSO)
    items = [path(smooth([(276, 196), (290, 212), (291, 250), (284, 250), (280, 214)]), o["shirt_light"]),
             path(smooth([(226, 236), (236, 238), (238, 300), (226, 300)]), o["shirt_dark"])]
    if o["top"] == "vest":
        vest_front = smooth([(266, 196), (282, 200), (290, 218), (292, 248), (288, 278), (283, 304), (262, 304),
                             (266, 262), (268, 226)])
        vest_back = smooth([(238, 196), (252, 192), (256, 230), (252, 270), (250, 304), (228, 304), (224, 270),
                            (226, 232), (230, 208)])
        items += [path(vest_back, o["vest"], INK, 1.6), path(vest_front, o["vest"], INK, 1.6),
                  path(smooth([(224, 236), (234, 238), (236, 300), (224, 300)]), o["vest_dark"]),
                  path(smooth([(280, 220), (290, 222), (290, 276), (282, 296)]), o["vest_light"])]
        for y in (220, 240, 260, 280):
            items.append(line([(228, y), (252, y + 2)], o["vest_dark"], 1.3))
            items.append(line([(268, y + 2), (290, y)], o["vest_dark"], 1.3))
        items.append(line([(266, 200), (264, 300)], "#9aa0a8", 1.4))  # the zip
        items.append(path(smooth([(274, 212, True), (282, 211, True), (282, 217, True), (274, 218, True)]), C["neon"]))
        items.append(path(smooth([(256, 186, True), (268, 192), (272, 206, True), (262, 198)]), o["shirt_light"], INK, 1.2))
    elif o["top"] == "hoodie":
        items += [path(smooth([(258, 252), (288, 250), (290, 284), (262, 286)]), o["shirt_dark"], INK, 1.4),
                  line([(262, 262), (286, 260)], o["shirt_light"], 1.2),
                  path(smooth([(272, 210, True), (286, 208, True), (286, 222, True), (272, 224, True)]), "#1d2b18"),
                  line([(276, 212), (282, 220)], C["neon"], 1.6), line([(282, 212), (276, 220)], C["neon"], 1.6),
                  line([(268, 194), (270, 230)], "#f2f2f2", 1.6), line([(276, 196), (278, 228)], "#f2f2f2", 1.6),
                  path(smooth([(222, 290, True), (292, 288, True), (292, 304, True), (222, 306, True)]), o["shirt_dark"]),
                  line([(224, 296), (290, 294)], o["shirt_light"], 1.0)]
    else:  # quarter zip
        items += [path(smooth([(252, 182, True), (272, 184, True), (276, 202), (262, 204), (254, 198)]), o["shirt_light"], INK, 1.4),
                  line([(268, 186), (270, 226)], "#9aa0a8", 1.6),
                  path(smooth([(268, 224, True), (274, 224, True), (273, 234, True), (269, 234, True)]), C["neon"], INK, 0.8),
                  path(smooth([(278, 214, True), (286, 213, True), (286, 219, True), (278, 220, True)]), C["neon"]),
                  line([(228, 222), (290, 220)], o["shirt_light"], 1.0)]
    body = [path(smooth([(250, 168), (266, 170), (270, 196), (248, 196)]), C["skin"], INK, 2 * OW)]
    if o["top"] == "hoodie":
        # the hood bunched behind the neck
        body.append(path(smooth([(226, 182), (240, 170), (258, 176), (262, 196), (240, 204), (226, 198)]), o["shirt"], INK, 2 * OW))
        body.append(line([(234, 184), (254, 186)], o["shirt_dark"], 2.0))
    body += outlined(sil, o["shirt"], items, "clip-torso")
    if o.get("lanyard"):
        body.append(line([(258, 188), (264, 220), (272, 246)], C["neon"], 3.0))
        body.append(line([(270, 190), (272, 222), (272, 246)], C["neon_dark"], 3.0))
        body.append(path(smooth([(262, 244, True), (282, 244, True), (282, 270, True), (262, 270, True)]), C["badge"], INK, 1.4))
        body.append(path(smooth([(265, 248, True), (279, 248, True), (279, 258, True), (265, 258, True)]), "#9fd8ff"))
        body.append(line([(266, 263), (278, 263)], "#888", 1.2))
    if o.get("chain"):
        body.append(line([(252, 188), (258, 212), (270, 224), (280, 210), (278, 192)], C["gold"], 2.6))
        body.append(path(smooth([(266, 222), (274, 222), (274, 232), (270, 236), (266, 232)]), C["gold"], INK, 1.0))
    part("torso", "Torso", "torso", "torso", 50, body)


def hips(o, C):
    sil = smooth([(228, 292, True), (284, 292, True), (288, 312), (282, 330), (232, 332), (226, 314)])
    items = [path(smooth([(224, 290, True), (290, 290, True), (290, 300, True), (224, 300, True)]), "#3a2a20"),
             path(smooth([(272, 291, True), (282, 291, True), (282, 300, True), (272, 300, True)]), "none", "#c0c4ca", 2.0)]
    if o["top"] == "hoodie":
        items = []
    part("hips", "Hips", "hips", "pelvis", 48, outlined(sil, o["pants"], items, "clip-hips"))


def leg(o, C, side):
    near = side == "near"
    zb = 30 if near else 20
    pants = o["pants"] if near else o["pants_dark"]
    hip, knee, ankle = J[f"{side}_hip"], J[f"{side}_knee"], J[f"{side}_ankle"]
    thigh = capsule(hip, knee, 22.0, 16.5)
    part(f"{side}-leg-u", "", f"{side}_leg_u", f"{side}_leg_u", zb + 2,
         outlined(thigh, pants, [line([(hip[0] + 9, hip[1] + 8), (knee[0] + 7, knee[1] - 6)], o["pants_light"], 3.4)], f"clip-{side}-thigh"))
    shin = capsule(knee, ankle, 16.5, 12.5)
    items = [line([(knee[0] + 7, knee[1] + 6), (ankle[0] + 6, ankle[1] - 8)], o["pants_light"], 3.0)]
    if o["top"] == "hoodie":
        items.append(path(smooth([(ankle[0] - 14, ankle[1] - 18, True), (ankle[0] + 14, ankle[1] - 18, True),
                                  (ankle[0] + 14, ankle[1] - 4, True), (ankle[0] - 14, ankle[1] - 4, True)]), o["pants_dark"]))
    part(f"{side}-leg-l", "", f"{side}_leg_l", f"{side}_leg_l", zb + 1, outlined(shin, pants, items, f"clip-{side}-shin"))
    ax, ay = ankle
    if o["shoe"] == "chunky":
        shoe = smooth([(ax - 16, ay - 14), (ax + 10, ay - 16), (ax + 24, ay - 6), (ax + 40, ay + 0), (ax + 44, ay + 8),
                       (ax + 44, ay + 18, True), (ax - 18, ay + 18, True), (ax - 19, ay + 2)])
        sole_h = 9
    else:
        shoe = smooth([(ax - 14, ay - 10), (ax + 8, ay - 12), (ax + 22, ay - 4), (ax + 38, ay + 2), (ax + 42, ay + 10),
                       (ax + 42, ay + 18, True), (ax - 16, ay + 18, True), (ax - 17, ay + 4)])
        sole_h = 6
    white = C["white"] if near else C["white_shadow"]
    items = [path(smooth([(ax - 20, ay + 18 - sole_h, True), (ax + 46, ay + 18 - sole_h, True), (ax + 46, ay + 20, True),
                          (ax - 20, ay + 20, True)]), o["sole"]),
             line([(ax + 4, ay - 6), (ax + 22, ay + 2)], C["white_shadow"], 1.6),
             path(smooth([(ax + 6, ay + 2), (ax + 22, ay - 2), (ax + 26, ay + 6), (ax + 10, ay + 8)]), C["neon"])]
    part(f"{side}-foot", "", f"{side}_foot", f"{side}_foot", zb + 3, outlined(shoe, white, items, f"clip-{side}-shoe"))


def arm(o, C, side):
    near = side == "near"
    zb = 80 if near else 10
    sleeve = o["shirt"] if near else o["shirt_dark"]
    skin = C["skin"] if near else C["far_skin"]
    sh, el, wr = J[f"{side}_shoulder"], J[f"{side}_elbow"], J[f"{side}_wrist"]
    long_sleeve = o["top"] in ("hoodie", "zip")
    upper = capsule(sh, el, 15.5, 12.5)
    part(f"{side}-arm-u", "", f"{side}_arm_u", f"{side}_arm_u", zb,
         outlined(upper, sleeve, [line([(sh[0] + 6, sh[1] + 4), (el[0] + 5, el[1] - 2)], o["shirt_light"], 3.0)], f"clip-{side}-arm-u"))
    fore = capsule(el, wr, 12.5, 10.0)
    if long_sleeve:
        cuff = [path(smooth([(wr[0] - 12, wr[1] - 12, True), (wr[0] + 12, wr[1] - 12, True), (wr[0] + 12, wr[1] + 12, True),
                             (wr[0] - 12, wr[1] + 12, True)]), o["shirt_dark"])]
        part(f"{side}-arm-l", "", f"{side}_arm_l", f"{side}_arm_l", zb - 2, outlined(fore, sleeve, cuff, f"clip-{side}-arm-l"))
    else:
        # sleeves rolled to the elbow
        part(f"{side}-arm-l", "", f"{side}_arm_l", f"{side}_arm_l", zb - 2,
             outlined(fore, skin, [path(smooth([(el[0] - 14, el[1] - 10), (el[0] + 14, el[1] - 10), (el[0] + 14, el[1] + 10),
                                                (el[0] - 14, el[1] + 10)]), o["shirt_light"])], f"clip-{side}-arm-l"))
    wx, wy = wr
    hand = smooth([(wx - 6, wy - 9), (wx + 10, wy - 11), (wx + 18, wy - 6), (wx + 20, wy + 4), (wx + 14, wy + 10),
                   (wx + 2, wy + 11), (wx - 6, wy + 7)])
    body = outlined(hand, skin, [line([(wx + 9, wy - 10), (wx + 11, wy + 9)], C["skin_shadow"], 1.2)], f"clip-{side}-hand")
    if near:
        # a phone, screen lit, held up to read
        ph = smooth([(wx + 6, wy - 30, True), (wx + 22, wy - 30, True), (wx + 22, wy + 2, True), (wx + 6, wy + 2, True)])
        body = [path(ph, "#111418", INK, 2.0), path(smooth([(wx + 8, wy - 27, True), (wx + 20, wy - 27, True),
                                                             (wx + 20, wy - 2, True), (wx + 8, wy - 2, True)]), "#3cd27a")] + body
        body.append(line([(wx + 10, wy - 22), (wx + 18, wy - 22)], "#e9fff0", 1.2))
        body.append(line([(wx + 10, wy - 17), (wx + 16, wy - 17)], "#e9fff0", 1.2))
    else:
        prop = o.get("prop_far")
        if prop == "watch":
            body.insert(0, path(smooth([(wx - 10, wy - 10, True), (wx - 2, wy - 10, True), (wx - 2, wy + 10, True), (wx - 10, wy + 10, True)]),
                                "#111418", INK, 1.2))
            body.insert(1, path(smooth([(wx - 9, wy - 4, True), (wx - 3, wy - 4, True), (wx - 3, wy + 4, True), (wx - 9, wy + 4, True)]), C["neon"]))
        elif prop == "can":
            body.insert(0, path(smooth([(wx + 4, wy - 4, True), (wx + 22, wy - 4, True), (wx + 22, wy + 30, True), (wx + 4, wy + 30, True)]),
                                "#16181b", INK, 2.0))
            body.insert(1, path(smooth([(wx + 6, wy + 6, True), (wx + 20, wy + 6, True), (wx + 20, wy + 16, True), (wx + 6, wy + 16, True)]), C["neon"]))
        elif prop == "cup":
            body.insert(0, path(smooth([(wx + 2, wy - 10, True), (wx + 24, wy - 10, True), (wx + 21, wy + 26, True), (wx + 5, wy + 26, True)]),
                                "#e8f5d8", INK, 2.0))
            body.insert(1, path(smooth([(wx + 4, wy - 2, True), (wx + 22, wy - 2, True), (wx + 21, wy + 24, True), (wx + 5, wy + 24, True)]), "#8fd16a"))
            body.insert(2, line([(wx + 16, wy - 10), (wx + 22, wy - 26)], "#f2f2f2", 2.2))
    part(f"{side}-hand", "", f"{side}_hand", f"{side}_hand", zb + 4, body)


def draw(key):
    o = OUTFITS[key]
    C = dict(BASE)
    svg.configure(dx=DX, dy=DY, ink=INK, ow=OW, colors=C)
    arm(o, C, "far")
    leg(o, C, "far")
    leg(o, C, "near")
    torso(o, C)
    hips(o, C)
    head(o, C)
    arm(o, C, "near")
    return svg.document(size=(W, H), design=f"tech-bro-human-{key}", layer_id="tech-bro-human", label="Tech bro (human draft, not cast)",
                        comment=["  <!-- KEPT, NOT CAST: a human tech-bro draft (2026-10-18), not registered in the cast.",
                                 "       Drawn by scripts/svg_art/uncast/tech_bro_human_drafts.py. -->"], joints=svg.joints_layer(J, {"head_top": HEAD_XF}))


if __name__ == "__main__":
    import resvg_py
    from PIL import Image, ImageDraw
    import io
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    tiles = []
    for key in OUTFITS:
        text = draw(key)
        p = out / f"tech_bro_human_{key}.svg"
        p.write_text(text)
        png = bytes(resvg_py.svg_to_bytes(svg_string=text.replace("720mm", "720").replace("640mm", "640")))
        im = Image.open(io.BytesIO(png)).convert("RGBA")
        tiles.append((OUTFITS[key]["label"], im))
    sheet = Image.new("RGBA", (440 * len(tiles), 520), (96, 104, 112, 255))
    d = ImageDraw.Draw(sheet)
    for i, (label, im) in enumerate(tiles):
        crop = im.crop((200, 120, 640, 640))
        sheet.alpha_composite(crop, (440 * i, 0))
        d.text((440 * i + 8, 8), label, fill=(255, 255, 0, 255))
    sheet.save(out / "tech_bro_human_drafts.png")
    print(out / "tech_bro_human_drafts.png")
