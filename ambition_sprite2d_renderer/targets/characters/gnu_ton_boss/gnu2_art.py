"""Armored Gnu2: cyber-psychic armor around the *actual* Giant Gnu drawing.

This is a standalone visual variant of GNU-ton's giant, not an altered copy
of its geometry. The scene borrows the Giant Gnu's piece placements (including
its moving head, pivoting horns, articulated arms, tail, and four jointed
legs), recolors their SVG fills without mutating the original art palette,
and places armor on the appropriate *same transforms*.

All coordinates are in the giant's 2x design space. Physics ledges, seams,
rig bones and gameplay character definitions are intentionally untouched.
The first deliverable is still SVG art: packing animations as a gameplay
sheet is a separate step.

Parody direction: a genetically "upgraded" gnu in a psychic containment
harness. Retain the distinctive gnu horns, long muzzle, hoofed lower body,
centaur shoulders and hand silhouette. Neural crown, ribbed crescent horn
collars, lavender skin, reactor chest, armored four legs, long synthetic
tail and restraint cables supply the science-fiction armored-clone joke.
"""
from __future__ import annotations

import re
from dataclasses import replace

from . import _pieces as pc
from . import _svg as svg
from . import giant_art as g

# Same framing as scripts/svg_art/giant_gnu_art.py.
VIEW = (0.0, -320.0, 1800.0, 1452.0)

# Keep strong ink contours and sufficiently large mechanical motifs for
# Ambition's flat, side-view sprites (not photorealistic armor).
A = dict(
    ink="#21192f", edge="#35304d", under="#38334d", graphite="#3d405d",
    mid="#666985", metal="#858ea8", bright="#c6cee0", pearl="#f0f2ff",
    recess="#22263d", violet="#7054a8", purple="#a574e2", glow="#dba2ff",
    glow_light="#f0deff", cyan="#64d8ee", cyan_light="#d0fbff",
    purple_shadow="#4b326c", dim="#496f89", steel_shadow="#555971",
)

# The Giant Gnu palette is mapped only in the generated SVG's piece strings.
# Neither g.C nor _svg.C is edited, so this can be used beside the real GNU-ton.
_FUR_TO_GNU2 = dict(
    fur="#acacc6", light="#d6d3e6", dark="#79778f", deep="#514e6e",
    far="#85839e", far_dark="#5d5b77", mane="#48445e",
    mane_light="#736f8e", face="#bdbece", face_light="#ebeaf4",
    blaze="#6f6688", nose="#77718c", nose_light="#b4b2c9",
    horn="#e4e4f1", horn_light="#ffffff", horn_shade="#bcb8d5",
    horn_deep="#817d9e", hoof="#454159", hoof_light="#827d96",
    iris="#bd77fa", iris_dark="#8152bc", pupil="#26153e",
    trim="#60cade", trim_dark="#3285a0", bronze="#858aa3",
    bronze_dark="#535770", gold="#a8afc6", gold_light="#d9e6f0",
    gold_dark="#737d9d", cloth="#694a90", cloth_dark="#3c2d64",
    iris_hot="#e38bff", flower="#e5e4f5", white="#f7f4ff",
)
_RECOLOR = {v.lower(): _FUR_TO_GNU2[k] for k, v in g.C.items() if k in _FUR_TO_GNU2}
_RECOLOR.update({"#ffffff": A["glow_light"]})
_HEX = re.compile(r"#[0-9a-fA-F]{6}\b")


def _recolor_svg(fragment: str) -> str:
    """Exact hex-token mapping; avoid replacing substrings in path data/IDs."""
    return _HEX.sub(lambda m: _RECOLOR.get(m.group().lower(), m.group()), fragment)


def _base_variant(scene: pc.Scene) -> pc.Scene:
    out = pc.Scene()
    for placed in scene.items:
        # Replace the original brush, not its tail pivot. The longer synthetic
        # tail follows that pivot in every supported pose.
        if placed.name in {"tail", "tail_brush"}:
            continue
        piece = replace(placed.piece, body=tuple(map(_recolor_svg, placed.piece.body)))
        out.add(placed.name, placed.z, piece, placed.m, placed.stretch)
    return out


def _shape(points, color, stroke=None, sw=5.2):
    return svg.path(svg.smooth(points), color, stroke or A["ink"], sw)


def _poly(points, color, stroke=None, sw=5.2):
    return svg.path(svg.poly(points), color, stroke or A["ink"], sw)


def _line(points, color=None, sw=5.0):
    return svg.line(points, color or A["cyan"], sw, closed=False)


def _round(cx, cy, rx, ry, color, stroke=None, sw=3.5):
    return svg.ellipse(cx, cy, rx, ry, color, stroke or A["ink"], sw)


def _node(x, y, r=10, color=None):
    return [
        _round(x, y, r + 4, r + 4, A["recess"], A["metal"], 3.6),
        _round(x, y, r, r, color or A["cyan"], A["ink"], 2.0),
        _round(x - r * .24, y - r * .28, r * .26, r * .26, A["cyan_light"], "none", 0),
    ]


def _piece(items, *, origin=(0.0, 0.0), reach=1000.0):
    return pc.Piece(tuple(items), origin=origin, reach=reach)


def _mount(scene, name, z, items, m=pc.IDENT, stretch=1.0, *, reach=1000.0):
    scene.add("gnu2-" + name, z, _piece(items, reach=reach), m, stretch)


def _synthetic_tail():
    """A long flexible violet conduit in place of the giant's hair brush."""
    centers = [(350, 718), (318, 758), (274, 794), (218, 834), (156, 842),
               (113, 814), (103, 754), (126, 692), (170, 672)]
    ribbon = svg.smooth(svg.tube(centers, 24, 32))
    items = [
        svg.path(ribbon, A["purple_shadow"], A["ink"], 7),
        _line([(340, 712), (300, 760), (250, 797), (190, 821), (143, 805), (132, 757),
               (150, 711), (175, 699)], A["purple"], 15),
        _line([(340, 702), (306, 744), (257, 781), (204, 806), (150, 792)], A["glow"], 5),
        _round(170, 675, 39, 38, A["violet"], A["ink"], 6),
        _round(161, 663, 20, 16, A["purple"], "none", 0),
        _round(154, 656, 6, 6, A["glow_light"], "none", 0),
    ]
    # Flexible joints / visible sensor rings emphasize synthetic construction.
    for a, b in [((313, 757), (329, 774)), ((264, 796), (282, 816)),
                 ((203, 832), (220, 852)), ((142, 799), (111, 814)),
                 ((113, 742), (91, 739))]:
        items.append(_line([a, b], A["metal"], 8))
    return items


def _barrel_plates():
    """Side hull segments, avoiding the platform top / cyan trim strip."""
    o = [
        # Deep inset under all plates to anchor them visually to the coat.
        _shape([(399, 672), (430, 574), (562, 507), (685, 486), (781, 507),
                (921, 568), (950, 686), (840, 768), (557, 781), (421, 750)], A["recess"], sw=8),
        # Hind thigh plate and leading diamond shield.
        _shape([(418, 641, True), (458, 578), (531, 541), (588, 561),
                (612, 623), (583, 712), (519, 740), (431, 715)], A["metal"], sw=6),
        _shape([(432, 638), (462, 585), (535, 556), (571, 569), (550, 624),
                (480, 651)], A["bright"], sw=0.0),
        _line([(458, 689), (504, 707), (555, 696)], A["steel_shadow"], 7),
        _shape([(600, 539, True), (664, 490), (742, 468), (820, 506),
                (834, 601), (767, 721), (653, 726), (608, 650)], A["graphite"], sw=6),
        _shape([(635, 531), (677, 504), (733, 487), (784, 518),
                (764, 584), (675, 598)], A["mid"], sw=4),
        _line([(627, 630), (685, 655), (761, 631), (808, 585)], A["cyan"], 7),
        _poly([(711, 673), (745, 656), (784, 665), (752, 695)], A["violet"], sw=3),
        _shape([(824, 523), (895, 532), (944, 595), (947, 677),
                (892, 729), (805, 721), (835, 655)], A["metal"], sw=6),
        _shape([(841, 549), (894, 551), (920, 593), (907, 624), (864, 624)], A["bright"], sw=0.0),
        _line([(831, 677), (876, 693), (914, 661)], A["dim"], 8),
    ]
    # A paired "II" biomarker on the flank: readable as clone no. 2 even at
    # half resolution, but not text dependent on installed fonts.
    for x in (474, 507):
        o.append(_poly([(x, 616), (x + 14, 610), (x + 14, 668), (x, 674)], A["cyan_light"], A["dim"], 2))
    for x, y in ((447, 694), (574, 678), (625, 612), (798, 545), (892, 686)):
        o.extend(_node(x, y, 5.5))
    return o


def _chest_armor():
    o = [
        # Side yokes peek beyond the chest but stop before the shoulder decks.
        _shape([(841, 507), (920, 487), (952, 545), (926, 682),
                (894, 747), (852, 714), (837, 612)], A["steel_shadow"], sw=7),
        _shape([(1153, 485), (1235, 513), (1258, 606), (1223, 717),
                (1190, 747), (1151, 680), (1132, 550)], A["steel_shadow"], sw=7),
        # Central breastplate is purposefully V shaped instead of a generic
        # rectangle, to preserve the long-neck / centaur silhouette.
        _shape([(946, 503, True), (1009, 476), (1065, 479), (1149, 503, True),
                (1170, 585), (1130, 707), (1042, 795, True),
                (954, 707), (915, 585)], A["graphite"], sw=8),
        _shape([(960, 521), (1020, 498), (1080, 501), (1133, 519),
                (1139, 564), (1043, 590), (943, 562)], A["metal"], sw=5),
        _poly([(961, 604), (1035, 632), (1039, 755), (989, 715)], A["mid"], sw=4),
        _poly([(1049, 632), (1123, 604), (1095, 714), (1049, 755)], A["mid"], sw=4),
        _line([(942, 563), (1042, 604), (1142, 561)], A["cyan"], 8),
        _line([(960, 683), (1042, 768), (1125, 685)], A["purple"], 8),
        _round(1042, 641, 55, 55, A["recess"], A["bright"], 8),
        _round(1042, 641, 39, 39, A["purple_shadow"], A["ink"], 5),
        _poly([(1042, 603), (1077, 639), (1042, 680), (1007, 639)], A["violet"], A["glow"], 5),
        _poly([(1042, 609), (1068, 640), (1042, 665), (1019, 638)], A["glow"], "none", 0),
        _poly([(1042, 618), (1052, 634), (1042, 646), (1033, 633)], A["glow_light"], "none", 0),
    ]
    for x in (900, 1186):
        for y in (553, 657):
            o.extend(_node(x, y, 7.5))
    return o


def _shoulder_armor(side):
    """An independent shoulder deck, whose top remains a straight walkable rail."""
    s = -1 if side == "left" else 1
    center = 878 if s == -1 else 1207
    # Use a local x coordinate about the midpoint, so both shoulder pods
    # are the same silhouette without requiring a negative-scale transform.
    def pt(x, y):
        return (center + s * x, y, True)

    outer = [pt(-74, 448), pt(-88, 423), pt(-116, 395), pt(-92, 502),
             pt(-67, 549), pt(-6, 562), pt(73, 518), pt(82, 456)]
    ridge = [pt(-81, 436), pt(-28, 425), pt(36, 423), pt(81, 436),
             pt(69, 451), pt(-73, 451)]
    o = [
        _shape(outer, A["graphite"], sw=7),
        _shape(ridge, A["bright"], sw=5),
        _poly([pt(-69, 460), pt(59, 462), pt(34, 514), pt(-35, 526)], A["metal"], sw=4),
        _line([pt(-70, 441), pt(67, 441)], A["cyan"], 8),
        _line([pt(-24, 475), pt(27, 476), pt(9, 495)], A["dim"], 5),
    ]
    for dx in (-53, 54):
        o.extend(_node(center + s * dx, 463, 6.0))
    return o


def _leg_armor(track: str, kind: str, upper: bool):
    far = "far" in track
    shell = A["steel_shadow"] if far else A["metal"]
    rim = A["mid"] if far else A["bright"]
    length = g.LEG_LENGTHS[kind][0 if upper else 1]
    if upper:
        o = [
            _shape([(-46, 8, True), (30, 6, True), (44, 42), (30, length * .72),
                    (3, length - 10), (-37, length * .83)], shell, sw=5),
            _shape([(-33, 17), (9, 16), (24, 34), (4, length * .54),
                    (-25, length * .70)], rim, sw=0),
            _line([(20, 37), (28, length * .42), (11, length * .73)], A["dim"], 5),
        ]
    else:
        o = [
            _shape([(-29, 3, True), (31, 3, True), (36, length * .42),
                    (29, length - 9), (-30, length - 5), (-34, length * .40)], shell, sw=5),
            _poly([(-21, 15), (17, 15), (24, length * .68), (-18, length * .66)], rim, sw=2),
            _line([(-24, length * .72), (25, length * .72)], A["cyan"], 7),
        ]
    return o


def _knee_armor():
    return [
        _round(0, 0, 37, 34, A["recess"], A["mid"], 5),
        _round(-1, -2, 23, 19, A["metal"], A["bright"], 3),
        _round(1, -3, 10, 10, A["purple"], A["ink"], 3),
    ]


def _hoof_armor():
    return [
        _poly([(-46, -15), (-36, -38), (42, -38), (55, -7),
               (45, 32), (-48, 31)], A["graphite"], sw=5),
        _poly([(-35, -29), (33, -29), (45, -7), (-39, -7)], A["metal"], sw=3),
        _line([(-33, -2), (37, -2)], A["cyan"], 7),
        _line([(2, 1), (7, 29)], A["steel_shadow"], 5),
    ]


def _arm_plate(upper):
    length = g.ARM_UPPER if upper else g.ARM_FORE
    width = 43 if upper else 35
    return [
        _shape([(-width, 11), (width * .65, 6), (width + 13, 42),
                (width + 7, length - 31), (2, length - 12),
                (-width + 3, length - 24), (-width - 9, 44)], A["graphite"], sw=6),
        _shape([(-width + 6, 18), (width * .45, 17), (width, 42),
                (width - 6, length * .55), (-width + 10, length * .57)], A["metal"], sw=2),
        _line([(-width + 9, length * .73), (width + 5, length * .73)], A["cyan"], 9),
        _line([(width * .4, 31), (width * .57, length * .47)], A["bright"], 5),
    ]


def _elbow_armor():
    return [
        _shape([(-44, -13, True), (40, -14, True), (49, 21),
                (12, 50), (-35, 39)], A["metal"], sw=6),
        _line([(-29, 4), (30, 4)], A["cyan"], 7),
    ]


def _gauntlet():
    return [
        _shape([(-72, -50), (-32, -74), (53, -67), (84, -20),
                (81, 40), (47, 70), (-55, 58), (-88, 11)], A["graphite"], sw=7),
        _shape([(-50, -51), (-12, -62), (43, -56), (63, -29),
                (58, -6), (-35, -14)], A["metal"], sw=2),
        _poly([(-76, 0), (-56, -20), (-17, -20), (-8, 12), (-40, 25), (-76, 23)], A["mid"], sw=4),
        _line([(-40, 41), (15, 49), (54, 37)], A["cyan"], 7),
        _round(5, -16, 16, 16, A["purple"], A["ink"], 4),
        _round(1, -21, 6, 6, A["glow_light"], "none", 0),
    ]


def _horn_rings():
    """A pair of metallic containment bands over each original curving horn."""
    cx, cy = g.HEAD
    k = g.K
    def P(s, x, y):
        return (cx + s * x * k, cy + y * k)
    o = []
    for s in (-1, 1):
        o += [
            _poly([P(s, 68, -113), P(s, 103, -108), P(s, 130, -89),
                   P(s, 121, -56), P(s, 86, -76)], A["graphite"], sw=5),
            _poly([P(s, 143, -98), P(s, 175, -92), P(s, 197, -64),
                   P(s, 183, -36), P(s, 154, -54)], A["metal"], sw=4),
            _line([P(s, 147, -94), P(s, 169, -86), P(s, 186, -63)], A["cyan"], 6),
            _poly([P(s, 243, -91), P(s, 266, -105), P(s, 286, -128),
                   P(s, 272, -150), P(s, 255, -125)], A["graphite"], sw=4),
        ]
        o.extend(_node(*P(s, 109, -80), 6))
    return o


def _head_armor():
    """A segmented neural crown that preserves BOTH eyes and the gnu muzzle."""
    cx, cy = g.HEAD
    k = g.K
    def P(x, y, hard=False):
        return (cx + x * k, cy + y * k, True) if hard else (cx + x * k, cy + y * k)
    o = [
        # Split crown above the original eyes, with a raised central antenna.
        _shape([P(-104, -88, True), P(-69, -142), P(-30, -153), P(0, -131),
                P(33, -154), P(78, -144), P(109, -83), P(91, -65),
                P(40, -87), P(0, -69), P(-37, -86), P(-90, -59)], A["graphite"], sw=6),
        _shape([P(-83, -97), P(-58, -129), P(-24, -138), P(-9, -124),
                P(-38, -97)], A["metal"], sw=2),
        _shape([P(23, -126), P(41, -138), P(69, -126), P(86, -96),
                P(34, -98)], A["metal"], sw=2),
        _poly([P(-25, -137), P(0, -150), P(27, -137),
               P(18, -96), P(0, -84), P(-18, -96)], A["violet"], sw=4),
        _poly([P(-8, -131), P(0, -140), P(9, -130), P(7, -104), P(0, -100), P(-7, -104)], A["glow"], sw=1.5),
        _line([P(-82, -80), P(-60, -77), P(-40, -83)], A["cyan"], 5),
        _line([P(35, -83), P(60, -77), P(88, -83)], A["cyan"], 5),
        # Cheek guards flank rather than cover the expressive face/eyes.
        _shape([P(-106, -11), P(-83, -1), P(-51, 47), P(-35, 97),
                P(-63, 117), P(-99, 68)], A["steel_shadow"], sw=4),
        _shape([P(101, 1), P(117, 23), P(143, 82), P(143, 122),
                P(113, 133), P(94, 82)], A["metal"], sw=4),
        _line([P(-88, 20), P(-68, 59), P(-45, 89)], A["cyan"], 5),
        _line([P(118, 44), P(132, 84), P(130, 112)], A["cyan"], 5),
        # Crown antenna: gnu horns remain the large silhouette; the antenna
        # is shorter so it does not look like an extra horn.
        _poly([P(-21, -140), P(-11, -185), P(11, -185), P(22, -140)], A["metal"], sw=5),
        _poly([P(-7, -174), P(0, -191), P(7, -174), P(0, -160)], A["glow"], sw=2),
    ]
    o.extend(_node(*P(-99, 65), 7.5, color=A["purple"]))
    o.extend(_node(*P(126, 92), 7.5, color=A["purple"]))
    return o


def _neck_collar():
    return [
        _shape([(946, 289), (991, 303), (1095, 302), (1145, 288),
                (1156, 348), (1112, 383), (972, 383), (932, 349)], A["recess"], sw=6),
        _poly([(948, 328), (992, 343), (1100, 340), (1140, 327),
               (1130, 362), (965, 362)], A["metal"], sw=4),
        _line([(966, 360), (1041, 370), (1124, 358)], A["cyan"], 7),
    ]


def armored_gnu2_scene(pose: dict, *, arms: bool = True) -> pc.Scene:
    """Layer the cybernetic armor on the same body/limb transforms as Giant Gnu.

    All `gnu2-*` placements are new; the base rig's transforms and animation
    coordinates stay untouched. This currently decorates *whole* limbs, not
    the short portal-cut pieces of the boss-specific attack animations.
    """
    original = g.scene_for(pose, arms=arms)
    out = _base_variant(original)
    by_name = {x.name: x for x in original.items}

    # Replace the original tail using its own exact pose transform.
    if "tail" in by_name:
        tail = by_name["tail"]
        _mount(out, "synth-tail", 19, _synthetic_tail(), tail.m, reach=950)

    for placed in original.items:
        name = placed.name
        if name == "beast":
            _mount(out, "flank-harness", 31, _barrel_plates(), placed.m, placed.stretch)
        elif name == "chest":
            _mount(out, "breastplate", 35, _chest_armor(), placed.m)
        elif name.endswith(("-upper", ":upper")) and (name.startswith("far-") or name.startswith("near-") or "hoof_right" in name):
            # Near foreleg is tagged `limb:hoof_right` by the original track map.
            kind = "hind" if "hind" in name else "fore-far" if "far-fore" in name else "fore-near"
            _mount(out, name + "-plate", placed.z + .7, _leg_armor(name, kind, upper=True), placed.m, placed.stretch, reach=500)
        elif name.endswith(("-lower", ":lower")) and (name.startswith("far-") or name.startswith("near-") or "hoof_right" in name):
            kind = "hind" if "hind" in name else "fore-far" if "far-fore" in name else "fore-near"
            _mount(out, name + "-shin", placed.z + .7, _leg_armor(name, kind, upper=False), placed.m, placed.stretch, reach=500)
        elif name.endswith(("-knee", ":knee")) and (name.startswith("far-") or name.startswith("near-") or "hoof_right" in name):
            _mount(out, name + "-joint", placed.z + .7, _knee_armor(), placed.m, reach=110)
        elif name.endswith(("-foot", ":foot")) and (name.startswith("far-") or name.startswith("near-") or "hoof_right" in name):
            _mount(out, name + "-boot", placed.z + .7, _hoof_armor(), placed.m, reach=180)
        elif name.startswith("limb:hand_") and name.endswith(":upper"):
            _mount(out, name + "-plate", 41, _arm_plate(True), placed.m, reach=500)
        elif name.startswith("limb:hand_") and name.endswith(":fore"):
            _mount(out, name + "-bracer", 41, _arm_plate(False), placed.m, reach=500)
        elif name.startswith("limb:hand_") and name.endswith(":tuft"):
            _mount(out, name + "-elbow", 41, _elbow_armor(), placed.m, reach=110)
        elif name.startswith("limb:hand_") and name.endswith(":fist"):
            _mount(out, name + "-gauntlet", 41, _gauntlet(), placed.m, reach=250)
        elif name == "epaulet_left":
            _mount(out, "shoulder-left", 47, _shoulder_armor("left"), placed.m)
        elif name == "epaulet_right":
            _mount(out, "shoulder-right", 47, _shoulder_armor("right"), placed.m)
        elif name == "neck":
            _mount(out, "collar", 49, _neck_collar(), placed.m)
        elif name == "horns":
            _mount(out, "horn-restraints", 57, _horn_rings(), placed.m)
        elif name == "head":
            _mount(out, "neural-helm", 61, _head_armor(), placed.m)
    return out


def armored_gnu2_svg(pose: dict, *, arms: bool = True, view=VIEW) -> str:
    """Export one vector pose; `view` is (x, y, width, height) in design units."""
    return pc.svg_of(armored_gnu2_scene(pose, arms=arms), view)


def preview_pose(stance: str = "sloped", expression: str | None = None) -> dict:
    """Static art pose, with the original gnu expressions and resting arms."""
    if stance not in g.STANCES:
        raise ValueError(f"Unknown gnu stance: {stance!r}; choose {sorted(g.STANCES)}")
    st = g.STANCES[stance]
    expr = expression or st["expr"]
    if expr not in g.EXPRESSIONS:
        raise ValueError(f"Unknown gnu expression: {expr!r}; choose {sorted(g.EXPRESSIONS)}")
    return dict(stance=st, expr=g.EXPRESSIONS[expr], head=(0.0, 0.0), dust=0.0)
