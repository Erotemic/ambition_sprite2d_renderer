#!/usr/bin/env python3
"""Programmatically author GNU-ton's scholar as a cleaner, flatter SVG rig.

This rebuild intentionally resets the design instead of iterating on the prior
accumulated version. The goals are:

- simpler editable geometry with fewer nodes and fewer decorative curves
- flatter, outline-driven color treatment
- a single readable nose solution (no duplicate nose tip highlight)
- a real pelvis bridge between torso and legs
- coat tails that live behind the body stack
- clearer part semantics for later Inkscape editing and rigging
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

import svgkit as svg
from scholar_svg_labels import annotate_for_inkscape
from svgkit import ellipse as E, line as L, path as P, smooth as S

HERE = Path(__file__).resolve().parents[2]
DEST = HERE / "ambition_sprite2d_renderer/data/characters/gnu_ton_scholar_villain/gnu_ton_scholar_villain.svg"
W, H = 510, 520
CENTER_X, GROUND_Y = 236.0, 478.0
INK = "#1a1620"
C = {
    "ink": INK,
    "coat": "#284e8f",
    "coat_dark": "#203a68",
    "coat_light": "#3c67ac",
    "gold": "#efc455",
    "gold_dark": "#a57934",
    "vest": "#b44650",
    "vest_dark": "#8a2f45",
    "skin": "#efb27e",
    "skin_dark": "#d19169",
    "skin_light": "#f7c796",
    "blush": "#d98c8c",
    "wig": "#eee2c0",
    "wig_light": "#faf1d7",
    "wig_shadow": "#d2c29c",
    "wig_dark": "#8c7c60",
    "linen": "#f6efdf",
    "linen_dark": "#cbc2ae",
    "pants": "#3a2d40",
    "pants_light": "#55455f",
    "stocking": "#f7f1e5",
    "boot": "#2a2832",
    "boot_light": "#514855",
    "book": "#6a2440",
    "book_light": "#95526a",
    "paper": "#fbefcf",
    "feather": "#eceae2",
    "feather_line": "#95a1b0",
    "shaft": "#b28a58",
    "eye": "#141a25",
    "mouth": "#61243c",
    "tongue": "#bb5b61",
    "tooth": "#fff5e9",
    "apple": "#c83d45",
    "leaf": "#5f8152",
}

J = {
    "pelvis": (192, 322), "neck": (194, 179), "head_top": (198, 89),
    "far_shoulder": (163, 211), "far_elbow": (145, 261), "far_wrist": (139, 300),
    "near_shoulder": (216, 214), "near_elbow": (249, 256), "near_wrist": (266, 223),
    "far_hip": (180, 322), "far_knee": (174, 381), "far_ankle": (170, 434),
    "near_hip": (203, 325), "near_knee": (211, 384), "near_ankle": (207, 434),
    "tail_far": (175, 309), "tail_far_tip": (144, 372),
    "tail_near": (209, 308), "tail_near_tip": (225, 375),
    "wig_queue": (158, 144), "wig_queue_tip": (135, 209),
    "star_halo": (200, 62), "star_halo_tip": (200, 37),
}


def poly(points):
    return S([(*xy, True) for xy in points])


def brush(d, color, sw=3):
    return P(d, "none", color, sw)


def star(cx, cy, radius):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        r = radius if i % 2 == 0 else radius * 0.45
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return poly(pts)


def piece(key, bone, z, silhouette, fill, details=(), width=4.0, label=None, extra=""):
    svg.part(key, label or key.replace("_", " ").title(), key, bone, z,
             [P(silhouette, fill, INK, width), *details], extra)


def decoration(key, bone, z, items, extra=""):
    svg.part(key, key.replace("_", " ").title(), key, bone, z, list(items), extra)


def swap(key, bone, z, items, channel, default=False):
    extra = f' data-rig-opacity="{channel}"'
    if default:
        extra += ' data-rig-default="1"'
    decoration(key, bone, z, items, extra)



# Accepted facial design: D2 from the eye-placement exploration sheet.
# Directions here describe the ACTOR (his own perspective), not pixel axes:
#   actor-right / canvas-left = larger near eye, closer to viewer
#   actor-left / canvas-right = smaller far eye, nearer the nose silhouette
# The near eye is intentionally much larger and slightly lower.
# These are SVG generator design coordinates before svgkit's +44/+32 shift.
D2_NEAR_EYE = (206.0, 139.3)
D2_FAR_EYE = (228.8, 135.4)


def draw():
    svg.configure(dx=44, dy=32, ink=INK, ow=1.55, colors=C)

    # Rear lower body
    piece("far_foot_art", "far_foot", 14,
          S([(152,427), (177,427), (194,435), (201,446), (150,446)]),
          C["boot"], [
              P(S([(156,432), (176,432), (191,439), (194,443), (157,442)]), C["boot_light"]),
              P(poly([(164,430), (176,430), (176,438), (164,438)]), C["gold"], INK, 1.5),
              L([(154,445), (198,445)], INK, 2),
          ], width=3.5)
    piece("far_shin", "far_leg_l", 12,
          S([(165,374), (181,374), (180,438), (164,438)]),
          C["stocking"], [
              P(S([(170,388), (176,389), (175,433), (169,433)]), C["linen"]),
              L([(165,392), (180,392)], C["linen_dark"], 1.6),
          ], width=3.3)
    piece("far_breeches", "far_leg_u", 13,
          S([(170,318), (186,316), (191,334), (186,386), (167,384), (165,334)]),
          C["pants"], [
              P(S([(173,330), (181,328), (179,378), (171,379)]), C["pants_light"]),
              L([(167,380), (184,382)], C["coat_dark"], 1.8),
          ], width=3.6)

    # Coat tails stay behind basically everything.
    piece("far_coat_tail", "tail_far", 9,
          S([(170,301), (184,301), (188,315), (181,356), (165,388), (147,392), (148,365), (159,326)]),
          C["coat"], [
              P(S([(174,307), (181,307), (180,347), (168,382), (153,386), (154,366), (163,332)]), C["coat_light"]),
              L([(150,389), (163,385), (175,364)], C["gold"], 1.9),
          ], width=3.7)
    piece("near_coat_tail", "tail_near", 10,
          S([(198,302), (214,302), (223,315), (228,351), (228,387), (214,390), (203,364), (198,330)]),
          C["coat"], [
              P(S([(204,308), (212,308), (220,321), (223,380), (216,383), (207,356), (203,334)]), C["coat_light"]),
              L([(217,387), (226,386), (221,374)], C["gold"], 1.9),
          ], width=3.7)

    # Queue
    piece("wig_queue", "wig_queue", 19,
          S([(158,140), (169,149), (165,179), (157,205), (143,215), (132,212), (134,183), (143,156)]),
          C["wig_shadow"], [
              P(S([(147,155), (158,163), (152,198), (139,208), (141,184)]), C["wig_light"]),
              L([(137,186), (157,191)], C["wig_dark"], 2.4),
              P(S([(141,186), (128,195), (135,181)]), C["coat_dark"], INK, 1.7),
              P(S([(150,190), (161,201), (162,182)]), C["coat_dark"], INK, 1.7),
          ], width=3.0)

    # Rear arm and props
    piece("far_arm_upper", "far_arm_u", 22,
          S([(156,204), (171,208), (168,228), (156,272), (138,268), (141,252), (149,220)]),
          C["coat"], [
              P(S([(154,214), (163,219), (154,259), (145,261)]), C["coat_light"]),
              L([(144,262), (153,265)], C["gold_dark"], 1.9),
          ], width=3.4)
    piece("far_arm_lower", "far_arm_l", 23,
          S([(136,255), (154,261), (151,311), (132,313), (129,305), (131,277)]),
          C["coat"], [
              P(S([(141,270), (149,272), (143,302), (135,304)]), C["coat_light"]),
              L([(133,298), (146,302)], C["gold"], 2.4),
          ], width=3.4)
    piece("far_cuff", "far_arm_l", 24,
          S([(128,299), (146,302), (145,315), (134,321), (125,314)]),
          C["linen"], [L([(129,309), (143,310)], C["linen_dark"], 1.4)], width=2.2)
    piece("principia_open_cover", "far_hand", 28.2,
          S([(103,281), (134,292), (166,281), (170,322), (138,341), (102,325)]),
          C["book"], [L([(138,292), (139,338)], C["gold"], 2.1)], width=2.6,
          extra=' data-rig-opacity="prop.book_open"')
    piece("principia_open_left", "far_hand", 28.4,
          S([(106,282), (132,289), (138,297), (138,329), (130,320), (106,318)]),
          C["paper"], [
              L([(112,294), (128,299)], C["gold_dark"], 1.4),
              L([(112,301), (128,306)], C["gold_dark"], 1.1),
              L([(111,308), (128,313)], C["gold_dark"], 1.1),
          ], width=2.2, extra=' data-rig-opacity="prop.book_open"')
    piece("principia_open_right", "far_hand", 28.6,
          S([(139,297), (142,289), (164,282), (166,316), (142,328), (139,329)]),
          C["linen"], [
              L([(147,300), (160,293)], C["gold_dark"], 1.4),
              L([(147,307), (160,300)], C["gold_dark"], 1.1),
              L([(146,314), (160,307)], C["gold_dark"], 1.1),
          ], width=2.2, extra=' data-rig-opacity="prop.book_open"')
    piece("principia_book", "far_hand", 29,
          S([(104,281), (137,284), (147,291), (151,353), (111,355), (105,349)]),
          C["book"], [
              P(S([(110,286), (142,289), (145,345), (112,347)]), C["book_light"]),
              P(poly([(143,289), (151,291), (156,350), (150,353)]), C["paper"], INK, 1.4),
              P(S([(118,296), (133,297), (138,339), (119,340)]), "none", C["gold"], 2.0),
              E(127,319,6.5,7.0,C["vest_dark"],C["gold"],1.8),
              L([(122,321), (127,313), (132,321), (126,328)], C["gold"], 1.8),
              L([(108,349), (146,351)], C["gold"], 1.7),
          ], width=2.8, extra=' data-rig-opacity="prop.book" data-rig-default="1"')
    piece("far_hand_fist", "far_hand", 27,
          S([(130,296), (143,295), (147,302), (144,312), (136,315), (129,311), (126,305)]),
          C["skin"], [
              P(S([(132,301), (140,300), (143,307), (136,312)]), C["skin_light"]),
              L([(131,305), (138,309)], C["skin_dark"], 1.4),
          ], width=2.3)

    # Core body with explicit pelvis bridge.
    piece("neck_base", "torso", 36,
          S([(180,161), (204,160), (205,199), (180,207), (173,195)]),
          C["skin"], [P(S([(180,178), (191,179), (190,201), (179,199)]), C["skin_dark"])], width=2.6)
    piece("torso_coat", "torso", 40,
          S([(158,201), (173,191), (205,193), (220,206), (223,246), (218,297), (205,318), (179,319), (161,304), (155,257), (155,223)]),
          C["coat"], [
              L([(170,203), (170,304)], C["coat_dark"], 2.0),
              L([(208,205), (210,300)], C["coat_dark"], 2.0),
          ], width=3.9)
    piece("pelvis_panel", "pelvis", 41,
          S([(172,303), (207,303), (215,316), (210,330), (176,331), (169,318)]),
          C["coat_dark"], [
              P(S([(177,307), (203,307), (208,318), (203,326), (180,326), (175,317)]), C["vest_dark"]),
              E(192,317,4.3,4.6,C["gold"],INK,1.2),
          ], width=3.1)
    piece("waistcoat", "torso", 42,
          S([(180,206), (201,206), (211,228), (206,304), (198,317), (182,315), (175,298), (174,231)]),
          C["vest"], [
              E(194,246,4.0,4.0,C["gold"],INK,1.2),
              E(194,270,4.0,4.0,C["gold"],INK,1.2),
              E(194,294,4.0,4.0,C["gold"],INK,1.2),
          ], width=3.3)
    piece("far_lapel", "torso", 43,
          S([(173,192), (186,205), (187,241), (176,251), (166,230), (164,208)]),
          C["coat_dark"], [L([(168,212), (177,240)], C["gold"], 2.2)], width=3.0)
    piece("near_lapel", "torso", 44,
          S([(201,192), (212,205), (213,240), (202,250), (194,232), (195,208)]),
          C["coat_dark"], [L([(206,212), (204,240)], C["gold"], 2.2)], width=3.0)
    piece("cravat", "torso", 45,
          S([(176,184), (188,184), (200,186), (204,200), (198,216), (197,235), (187,228), (185,214), (178,214), (174,202)]),
          C["linen"], [
              P(S([(180,189), (189,195), (190,211), (183,216)]), C["linen"]),
              L([(192,202), (197,211), (193,223)], C["linen_dark"], 1.4),
          ], width=2.5)
    piece("coat_pin", "torso", 46,
          poly([(211,237), (216,241), (211,246), (206,241)]),
          C["gold"], [P(poly([(211,239), (213,241), (211,243), (209,241)]), C["gold_dark"], INK, 1.0)], width=2.0)

    # Front legs
    piece("near_breeches", "near_leg_u", 50,
          S([(196,319), (211,322), (219,343), (222,380), (209,392), (197,386), (193,355)]),
          C["pants"], [
              P(S([(204,334), (212,345), (215,376), (209,383)]), C["pants_light"]),
              L([(201,384), (217,383)], C["coat_dark"], 1.8),
          ], width=3.6)
    piece("near_shin", "near_leg_l", 51,
          S([(201,378), (221,380), (219,439), (200,439), (197,431), (201,396)]),
          C["stocking"], [
              P(S([(208,397), (214,397), (211,432), (206,432)]), C["linen"]),
              L([(202,392), (220,396)], C["linen_dark"], 1.6),
          ], width=3.3)
    piece("near_shoe", "near_foot", 52,
          S([(198,427), (213,427), (223,435), (244,439), (247,449), (194,449), (192,444)]),
          C["boot"], [
              P(S([(200,431), (212,431), (221,439), (240,441), (243,445), (198,445)]), C["boot_light"]),
              P(poly([(201,430), (214,431), (214,439), (201,438)]), C["gold"], INK, 1.5),
              L([(194,448), (242,448)], INK, 2),
          ], width=3.5)

    # Head and hair. Keep the face holistic and round; one actual nose shape.
    piece("wig_back_mass", "head", 57,
          S([(170,144), (157,129), (154,111), (159,92), (170,79), (185,70), (202,69), (218,73), (231,82), (239,97), (240,116), (235,133), (220,140), (198,138), (181,138)]),
          C["wig_shadow"], [
              P(S([(159,109), (167,88), (181,76), (199,73), (217,77), (230,88), (235,103), (234,122), (220,131), (199,129), (175,134)]), C["wig"]),
              P(S([(165,105), (174,86), (191,76), (202,79), (191,89), (174,104)]), C["wig_light"]),
          ], width=3.4)
    piece("head_face", "head", 60,
          S([(174,121), (188,112), (204,108), (219,110), (231,118), (239,131), (241,147), (237,163), (228,176), (214,184), (198,187), (185,184), (174,177), (166,163), (164,147), (167,133)]),
          C["skin"], [
              P(S([(206,113), (220,116), (231,128), (220,128)]), C["skin_light"]),
              E(196,160,6.2,4.8,C["blush"]),
              P(poly([(226,148), (238,154), (227,162)]), C["skin_dark"], INK, 1.6),
              E(174,148,6.6,8.9,C["skin"],INK,2.2),
              L([(174,146), (176,150), (174,153)], C["skin_dark"], 1.5),
          ], width=3.8)
    piece("wig_crown", "head", 66,
          S([(160,124), (158,106), (161,91), (170,80), (182,73), (196,70), (211,72), (224,79), (233,88), (238,102), (239,118), (232,128), (218,126), (206,130), (195,126), (186,120), (178,124), (168,133), (163,138)]),
          C["wig"], [
              P(S([(162,107), (171,88), (182,77), (194,74), (203,82), (188,86), (172,104)]), C["wig_light"]),
              P(S([(211,78), (224,86), (230,101), (229,114), (219,114), (212,104)]), C["wig_shadow"]),
              L([(181,80), (189,87), (187,96)], C["wig_shadow"], 1.8),
              L([(214,85), (221,96), (214,105)], C["wig_dark"], 1.6),
              L([(166,110), (169,122)], C["wig_shadow"], 1.6),
          ], width=3.4)
    for idx, (x, y, rx, ry) in enumerate(((163,124,10,10), (159,143,11,11), (158,163,11,11))):
        decoration(f"wig_curl_{idx}", "head", 67 + idx * 0.1, [
            E(x, y, rx, ry, C["wig"], INK, 2.6),
            E(x - 2, y - 2, rx * 0.56, ry * 0.52, C["wig_light"]),
            P(S([(x + 3, y - 5), (x + 6, y - 1), (x + 3, y + 3),
                 (x - 1, y + 4), (x - 3, y + 1), (x - 1, y - 2), (x + 1, y - 2)], closed=False),
              "none", C["wig_dark"], 1.6),
        ])

    # The D2 layout is shared by every expression. Eye anatomy (right/left)
    # describes the character, and near/far describe relative camera depth.
    near_x, near_y = D2_NEAR_EYE  # actor-right eye, canvas-left
    far_x, far_y = D2_FAR_EYE     # actor-left eye, canvas-right

    swap("eye_angry", "head", 71, [
        E(near_x, near_y, 8.7, 7.3, C["linen"], INK, 2.1),
        E(near_x + 2.7, near_y + 0.6, 3.05, 3.5, C["eye"]),
        E(near_x + 3.45, near_y - 0.5, 0.95, 1.0, C["linen"]),
        L([(near_x - 7, near_y - 9.5), (near_x + 6.5, near_y - 8)], INK, 2.4),
        E(far_x, far_y, 4.7, 5.0, C["linen"], INK, 1.75),
        E(far_x + 1.25, far_y + 0.55, 1.6, 2.1, C["eye"]),
        E(far_x + 1.65, far_y - 0.2, 0.5, 0.55, C["linen"]),
        L([(far_x - 3.5, far_y - 7.4), (far_x + 3.8, far_y - 6.8)], INK, 1.75),
    ], "eye.angry")
    swap("eye_open", "head", 71, [
        E(near_x, near_y, 9.3, 8.2, C["linen"], INK, 2.05),
        E(near_x + 3.0, near_y + 0.5, 3.2, 3.8, C["eye"]),
        E(near_x + 3.75, near_y - 0.6, 1.0, 1.1, C["linen"]),
        L([(near_x - 7, near_y - 11), (near_x - 1.2, near_y - 12.1),
           (near_x + 5.7, near_y - 11)], INK, 1.9),
        E(far_x, far_y, 5.0, 5.5, C["linen"], INK, 1.75),
        E(far_x + 1.3, far_y + 0.45, 1.75, 2.25, C["eye"]),
        E(far_x + 1.7, far_y - 0.4, 0.58, 0.65, C["linen"]),
        L([(far_x - 4.2, far_y - 7.8), (far_x + 3.7, far_y - 7.4)], INK, 1.45),
    ], "eye.open", True)
    swap("eye_surprised", "head", 71, [
        E(near_x, near_y, 9.7, 10.0, C["linen"], INK, 2.25),
        E(near_x + 2.8, near_y + 0.6, 3.5, 4.3, C["eye"]),
        E(near_x + 3.7, near_y - 0.9, 1.1, 1.2, C["linen"]),
        L([(near_x - 7, near_y - 14.8), (near_x + 6.1, near_y - 14.5)], INK, 1.85),
        E(far_x, far_y, 5.4, 6.3, C["linen"], INK, 1.85),
        E(far_x + 1.2, far_y + 0.7, 1.95, 2.7, C["eye"]),
        E(far_x + 1.7, far_y - 0.6, 0.6, 0.72, C["linen"]),
        L([(far_x - 4.1, far_y - 10.2), (far_x + 4.0, far_y - 10.0)], INK, 1.6),
    ], "eye.surprised")
    swap("eye_shut", "head", 71, [
        L([(near_x - 8.2, near_y), (near_x - 0.5, near_y + 3.0),
           (near_x + 8.0, near_y)], INK, 2.65),
        L([(far_x - 4.8, far_y), (far_x, far_y + 1.5),
           (far_x + 4.4, far_y)], INK, 1.95),
        L([(near_x - 7.0, near_y - 9.0), (near_x + 6.4, near_y - 9.0)], INK, 2.1),
        L([(far_x - 4, far_y - 8.0), (far_x + 4, far_y - 7.6)], INK, 1.4),
        L([(near_x - 8.0, near_y + 1.5), (near_x - 10.5, near_y + 4)], INK, 1.5),
    ], "eye.shut")
    swap("eye_dead", "head", 71, [
        L([(near_x - 6.2, near_y - 5.8), (near_x + 6.2, near_y + 6.2)], INK, 2.7),
        L([(near_x - 6.2, near_y + 6.2), (near_x + 6.2, near_y - 5.8)], INK, 2.7),
        L([(far_x - 3.7, far_y - 4.3), (far_x + 3.7, far_y + 4.5)], INK, 1.85),
        L([(far_x - 3.7, far_y + 4.5), (far_x + 3.7, far_y - 4.3)], INK, 1.85),
        L([(near_x - 7, near_y - 10.5), (near_x + 6, near_y - 10.2)], INK, 1.9),
        L([(far_x - 4.2, far_y - 8.2), (far_x + 3.7, far_y - 7.9)], INK, 1.4),
    ], "eye.dead")
    swap("eye_dizzy", "head", 71, [
        P(S([(near_x - 7, near_y), (near_x - 4, near_y - 6),
             (near_x + 2, near_y - 7), (near_x + 8, near_y - 4),
             (near_x + 8, near_y + 3), (near_x + 3, near_y + 7),
             (near_x - 3, near_y + 6), (near_x - 5, near_y + 2),
             (near_x - 2, near_y - 3), (near_x + 4, near_y - 2),
             (near_x + 4, near_y + 3), (near_x + 1, near_y + 4),
             (near_x - 1, near_y + 1), (near_x, near_y - 1)]), "none", INK, 2.8),
        P(S([(far_x - 4, far_y), (far_x - 2, far_y - 4),
             (far_x + 2, far_y - 4.5), (far_x + 5, far_y - 1.5),
             (far_x + 4.5, far_y + 3), (far_x + 1, far_y + 5),
             (far_x - 2, far_y + 2), (far_x - 1, far_y - 1),
             (far_x + 2, far_y - 1), (far_x + 2, far_y + 1),
             (far_x, far_y + 1.5)]), "none", INK, 1.9),
    ], "eye.dizzy")
    swap("mouth_closed", "head", 72, [L([(220,166), (225,168), (230,166)], INK, 2.0)], "mouth.closed", True)
    swap("mouth_smile", "head", 72, [L([(219,166), (224,170), (230,166)], INK, 2.0)], "mouth.smile")
    swap("mouth_open", "head", 72, [
        P(S([(221,163), (229,163), (231,168), (229,174), (223,174), (220,170)]), C["mouth"], INK, 2.0),
        P(S([(223,164), (229,164), (229,167), (223,167)]), C["tooth"]),
    ], "mouth.open")
    swap("mouth_wavy", "head", 72, [P(S([(218,167), (221,164), (225,168), (229,164), (232,167)]), "none", INK, 2.3)], "mouth.wavy")
    swap("mouth_grit", "head", 72, [
        P(S([(220,163), (232,163), (232,169), (221,170)]), C["tooth"], INK, 2.0),
        L([(224,166), (231,166)], C["mouth"], 1.1),
    ], "mouth.grit")

    # Front arm and quill
    piece("near_arm_upper", "near_arm_u", 78,
          S([(208,206), (225,204), (239,220), (252,240), (256,254), (247,268), (237,265), (224,244), (207,224)]),
          C["coat"], [
              P(S([(219,211), (235,226), (248,253), (245,259), (225,238)]), C["coat_light"]),
              L([(237,259), (252,255)], C["gold_dark"], 2.0),
          ], width=3.4)
    piece("near_arm_lower", "near_arm_l", 79,
          S([(244,251), (261,254), (265,247), (269,231), (276,220), (270,210), (259,212), (253,230)]),
          C["coat"], [
              P(S([(256,252), (263,244), (272,219), (265,216), (255,234)]), C["coat_light"]),
              L([(261,220), (273,223)], C["gold"], 2.5),
          ], width=3.4)
    piece("near_cuff", "near_arm_l", 80,
          S([(260,214), (272,215), (279,225), (272,234), (261,230), (257,222)]),
          C["linen"], [L([(264,228), (275,227)], C["linen_dark"], 1.4)], width=2.2)
    piece("quill", "near_hand", 82,
          S([(266,231), (271,218), (277,199), (285,180), (292,163), (297,149), (301,135), (308,117), (316,122), (314,139), (309,154), (303,168), (293,183), (283,200), (274,222)]),
          C["feather"], [
              P(S([(284,181), (291,164), (298,148), (305,130), (311,125), (310,139), (304,156), (296,172)]), C["linen"]),
              P(S([(266,228), (270,227), (272,234), (267,236)]), C["shaft"]),
              L([(269,231), (307,123)], C["shaft"], 2.6),
              L([(285,177), (279,168)], C["feather_line"], 1.8),
              L([(292,166), (301,159)], C["feather_line"], 1.6),
              L([(297,152), (308,144)], C["feather_line"], 1.6),
              L([(303,140), (313,133)], C["feather_line"], 1.4),
          ], width=2.9, extra=' data-rig-opacity="prop.quill" data-rig-default="1"')
    piece("near_hand_fist", "near_hand", 84,
          S([(258,217), (269,210), (279,214), (282,221), (276,229), (268,230), (260,228)]),
          C["skin"], [
              P(S([(262,219), (269,215), (275,216), (270,221)]), C["skin_light"]),
              L([(267,223), (275,225)], C["skin_dark"], 1.6),
          ], width=2.3)

    swap("dizzy_stars", "star_halo", 96,
         [P(star(x, y, r), C["gold"], INK, 2.0)
          for x, y, r in ((154, 66, 13), (208, 45, 15), (255, 79, 12))], "fx.stars")
    swap("flying_apple", "head", 97, [
        E(277,157,11,10,C["apple"],INK,2.4),
        E(273,153,3.0,2.5,C["skin_light"]),
        L([(278,148), (280,142)], INK, 1.8),
        P(S([(280,143), (291,139), (286,148)]), C["leaf"], INK, 1.3),
    ], "prop.apple")

    source = svg.document(
        size=(W, H), design="gnu-ton-scholar-v2-clean-rebuild",
        layer_id="scholar-three-quarter", label="GNU-ton Scholar - Three Quarter",
        comment=["<!-- Clean rebuild: flatter, simpler, more editable programmatic SVG -->"],
        joints=svg.joints_layer(J),
    )
    return annotate_for_inkscape(source)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", type=Path, default=DEST)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(draw(), encoding="utf8")
    print(f"wrote {args.output} ({len(svg.PARTS)} independently addressable SVG part layers)")


if __name__ == "__main__":
    main()
