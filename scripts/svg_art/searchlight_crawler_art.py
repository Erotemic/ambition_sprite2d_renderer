#!/usr/bin/env python3
"""Write the first Searchlight Crawler vector drawing.

Run from tools/ambition_sprite2d_renderer:

    uv run python scripts/svg_art/searchlight_crawler_art.py

The SVG is the art source after the first write. The script does not replace
artist edits unless ``--force`` is given. Rebuild the rig after a new draft.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
SVG_PATH = (
    ROOT
    / "ambition_sprite2d_renderer/data/characters/searchlight_crawler/searchlight_crawler.svg"
)
VIEW = "Searchlight Crawler - Side"
GROUND_Y = 419.0
CANVAS = (680, 480)

SVG_NS = "http://www.w3.org/2000/svg"
INK_NS = "http://www.inkscape.org/namespaces/inkscape"
SOD_NS = "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
ET.register_namespace("", SVG_NS)
ET.register_namespace("inkscape", INK_NS)
ET.register_namespace("sodipodi", SOD_NS)

INK = "#17212a"
DEEP = "#26343e"
BODY = "#526471"
PLATE = "#8393a0"
RIM = "#a9b6bc"
EDGE = "#d0dbd6"
BRASS = "#ad835a"
BRASS_HI = "#e4bd76"
LAMP = "#eafcdb"
RED = "#d8574d"

# The four leg pairs have different reach and height. The side view draws
# the distant set behind the hull and the near set above the hull. Every leg
# is a four-link chain: shoulder, raised femur, long tibia, and hooked foot.
# A tuple stores hip, shoulder, knee, ankle, and tip in SVG coordinates.
LEG_POINTS = {
    "far_rear_outer": ((274, 312), (233, 276), (132, 191), (117, 347), (98, 414)),
    "far_rear_inner": ((283, 321), (246, 294), (191, 241), (183, 369), (163, 418)),
    "far_front_inner": ((351, 322), (379, 294), (429, 231), (451, 368), (471, 419)),
    "far_front_outer": ((366, 309), (409, 279), (487, 184), (548, 346), (566, 416)),
    "near_rear_outer": ((263, 323), (219, 283), (92, 204), (76, 349), (49, 416)),
    "near_rear_inner": ((290, 331), (254, 302), (208, 252), (191, 374), (174, 420)),
    "near_front_inner": ((348, 330), (387, 297), (454, 246), (489, 369), (509, 420)),
    "near_front_outer": ((372, 321), (421, 278), (534, 212), (577, 349), (605, 416)),
}
SEGMENTS = ("coxa", "femur", "tibia", "tarsus")

# The list is shared by the SVG and the rig builder. The artist can move the
# joint markers with a matching edit to the draft's geometry and joint table.
JOINTS = {
    "body": (None, 322.0, 312.0),
    "light": ("body", 417.0, 259.0),
    "antenna": ("body", 291.0, 249.0),
    "shutter_upper": ("light", 454.0, 234.0),
    "shutter_lower": ("light", 454.0, 282.0),
    "exhaust_hatch": ("body", 247.0, 277.0),
}
for leg, chain in LEG_POINTS.items():
    parent = "body"
    for segment, point in zip(SEGMENTS, chain):
        name = f"{leg}_{segment}"
        JOINTS[name] = (parent, float(point[0]), float(point[1]))
        parent = name

# (SVG group id, editor label, rig part name, rig bone, draw order, alpha channel)
LAYERS = []
for leg in LEG_POINTS:
    if leg.startswith("far_"):
        for i, segment in enumerate(SEGMENTS):
            LAYERS.append((f"part-{leg.replace('_', '-')}-{segment}",
                           f"{leg.replace('_', ' ').title()} / {segment.title()}",
                           f"{leg}_{segment}", f"{leg}_{segment}",
                           12 + list(LEG_POINTS).index(leg) * 5 + i, None))

LAYERS.extend([
    ("part-hull", "Armored Hull", "hull", "body", 101, None),
    ("part-antenna", "Alarm Mast", "antenna_part", "antenna", 107, None),
    ("part-beacon-halo", "Alarm Flash", "beacon_halo", "antenna", 108, "beacon_visible"),
    ("part-exhaust-hatch", "Rear Vent Hatch", "exhaust_hatch_part", "exhaust_hatch", 112, None),
    ("part-exhaust-glow", "Rear Vent Heat", "exhaust_glow", "body", 113, "exhaust_visible"),
    ("part-search-cone", "Wide Search Cone", "search_cone", "light", 205, "beam_visible"),
    ("part-search-cone-narrow", "Focused Search Cone", "focus_cone", "light", 206, "focus_visible"),
    ("part-lamp", "Searchlight Assembly", "lamp", "light", 210, None),
    ("part-lamp-alert", "Alert Iris", "lamp_alert", "light", 212, "alert_visible"),
    ("part-shutter-upper", "Upper Iris Shutter", "shutter_upper_part", "shutter_upper", 215, None),
    ("part-shutter-lower", "Lower Iris Shutter", "shutter_lower_part", "shutter_lower", 216, None),
])

for leg in LEG_POINTS:
    if leg.startswith("near_"):
        for i, segment in enumerate(SEGMENTS):
            LAYERS.append((f"part-{leg.replace('_', '-')}-{segment}",
                           f"{leg.replace('_', ' ').title()} / {segment.title()}",
                           f"{leg}_{segment}", f"{leg}_{segment}",
                           140 + list(LEG_POINTS).index(leg) * 5 + i, None))


def node(parent: ET.Element, name: str, **attributes: object) -> ET.Element:
    return ET.SubElement(parent, f"{{{SVG_NS}}}{name}", {
        key: str(value) for key, value in attributes.items()
    })


def layer(parent: ET.Element, identity: str, label: str) -> ET.Element:
    return node(parent, "g", id=identity, **{f"{{{INK_NS}}}label": label})


def path(group: ET.Element, data: str, fill: str, stroke: str = INK,
         width: float = 3.5, **extra: object) -> None:
    node(group, "path", d=data, fill=fill, stroke=stroke, **{"stroke-width": width,
         "stroke-linejoin": "round", "stroke-linecap": "round"}, **extra)


def circle(group: ET.Element, center: tuple[float, float], radius: float,
           fill: str, stroke: str = INK, width: float = 3.0) -> None:
    node(group, "circle", cx=center[0], cy=center[1], r=radius, fill=fill,
         stroke=stroke, **{"stroke-width": width})


def point(xy: tuple[float, float]) -> str:
    return f"{xy[0]:.1f},{xy[1]:.1f}"


def shape(points: list[tuple[float, float]]) -> str:
    return "M " + " L ".join(point(p) for p in points) + " Z"


def segment_art(g: ET.Element, start: tuple[float, float], end: tuple[float, float],
                kind: str, near: bool, outer: bool) -> None:
    """Build one metal leg link. Its SVG group moves with one rig bone."""
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dy)
    ux, uy = dx / length, dy / length
    nx, ny = -uy, ux

    def offset(t: float, n: float) -> tuple[float, float]:
        return (start[0] + t * dx + n * nx, start[1] + t * dy + n * ny)

    widths = {
        "coxa": (14.5, 10.5),
        "femur": (11.0, 8.0),
        "tibia": (8.5, 5.7),
        "tarsus": (7.2, 1.3),
    }
    w0, w1 = widths[kind]
    if outer and near:
        w0 *= 1.10
        w1 *= 1.10
    color = ("#9fb0b6" if near else "#627684")
    edge = ("#d8e5de" if near else "#91a7ae")
    joint = ("#b39a78" if near else "#806b55")
    # A stepped metal rail is easier to read than a rounded tube at small size.
    panel = [
        offset(0.02, w0 / 2), offset(0.21, w0 / 2 + 1.7),
        offset(0.77, w1 / 2 + 1.0), offset(0.97, w1 / 2),
        offset(0.98, -w1 / 2), offset(0.77, -w1 / 2 - 1.0),
        offset(0.21, -w0 / 2 - 1.7), offset(0.02, -w0 / 2),
    ]
    path(g, shape(panel), color, width=3.4 if near else 3.1)
    if kind != "tarsus":
        path(g, f"M {point(offset(0.19, w0 * 0.20))} L {point(offset(0.78, w1 * 0.20))}",
             "none", edge, 2.4)
        path(g, f"M {point(offset(0.26, -w0 * 0.18))} L {point(offset(0.63, -w1 * 0.18))}",
             "none", DEEP, 2.1)
        # A narrow actuator runs beside the long shin and the raised femur.
        if kind in ("femur", "tibia"):
            path(g, f"M {point(offset(0.30, -w0 * 0.42))} L {point(offset(0.75, -w1 * 0.42))}",
                 "none", BRASS if near else DEEP, 2.1)
    else:
        # The hooked, sharp terminal claw is visually separate from its ankle.
        tip = offset(1.0, 0.0)
        path(g, f"M {point(offset(0.79, 0.0))} L {point((tip[0] + ux * 7, tip[1] + uy * 7))}",
             "none", INK, 2.5)
    circle(g, start, 9.0 if kind == "coxa" else (8.2 if kind == "femur" else 6.7),
           DEEP, INK, 3.1)
    circle(g, start, 4.0 if kind == "coxa" else 3.1,
           joint, DEEP, 1.5)
    if kind in ("femur", "tibia"):
        circle(g, end, 7.8 if kind == "femur" else 6.8, DEEP, INK, 2.4)
        circle(g, end, 3.0, BRASS_HI if near else "#9c9180", DEEP, 1.3)


def draw_body(view: ET.Element) -> None:
    hull = layer(view, "part-hull", "Armored Hull")
    under = layer(hull, "body-under", "Underframe")
    path(under, "M 255,299 L 280,269 L 363,268 L 406,291 L 391,332 L 345,350 L 278,345 L 245,320 Z",
         DEEP, width=5.7)
    path(under, "M 261,308 L 252,323 L 276,348 L 348,353 L 382,339 L 388,322",
         "none", "#131b22", 6)
    # Rear piston drive, narrow shoulder rails, and underside pressure cylinder.
    path(under, "M 236,297 L 258,277 L 287,279 L 285,318 L 257,326 L 233,312 Z",
         BODY, width=4.5)
    path(under, "M 249,283 L 277,290 M 250,301 L 272,308", "none", RIM, 3)
    path(under, "M 285,344 L 338,350 L 359,344", "none", BRASS, 5)
    for x, y in ((263, 332), (317, 344), (358, 337)):
        circle(under, (x, y), 5.2, "#687e88", INK, 2.2)

    armor = layer(hull, "body-armor", "Faceted Shell")
    # Separate bevel planes instead of one large round silhouette.
    path(armor, "M 251,289 L 267,268 L 313,254 L 360,263 L 391,280 L 402,308 "
         "L 379,329 L 344,339 L 302,335 L 270,326 L 249,307 Z",
         BODY, width=5.4)
    path(armor, "M 267,269 L 313,254 L 357,263 L 365,285 L 332,302 L 285,296 Z",
         PLATE, width=3.6)
    path(armor, "M 256,309 L 277,316 L 310,322 L 306,335 L 269,326 Z",
         "#40525f", width=3.1)
    path(armor, "M 337,305 L 375,285 L 392,296 L 383,320 L 344,334 L 318,323 Z",
         "#627782", width=3.4)
    path(armor, "M 274,279 L 309,268 L 345,276", "none", EDGE, 4.2)
    path(armor, "M 332,312 L 369,299", "none", RIM, 3.0)
    # Angular back fairing and exhaust slits break the barrel silhouette.
    path(armor, "M 231,282 L 242,267 L 272,266 L 284,282 L 266,303 L 236,301 Z",
         DEEP, width=4)
    for x in (246, 257, 268):
        path(armor, f"M {x},276 L {x + 5},285", "none", RED, 3.2)

    marks = layer(hull, "body-markings", "Fasteners and Warning Stripe")
    path(marks, "M 307,269 L 322,274 L 325,295 L 311,300 Z", "#c35343", INK, 2.0)
    path(marks, "M 314,275 L 318,277 L 319,292 L 314,291 Z", EDGE, "none", 0)
    for x, y in ((275, 289), (294, 314), (345, 279), (374, 314), (362, 328)):
        circle(marks, (x, y), 4.0, BRASS, INK, 1.7)
    path(marks, "M 279,320 L 291,324 M 364,281 L 376,286", "none", "#24323a", 2.0)
    # The gimbal is part of the body, so the lamp can turn independently.
    path(marks, "M 365,282 L 390,253 L 419,259", "none", INK, 16)
    path(marks, "M 365,282 L 390,253 L 419,259", "none", RIM, 9)
    circle(marks, (391, 255), 10, DEEP, INK, 3.0)
    circle(marks, (391, 255), 4, BRASS_HI, INK, 1)
    # Flexible harness loops from the drive to the lamp and mast.
    path(marks, "M 272,269 C 277,245 310,239 328,255 C 343,266 353,243 379,240",
         "none", INK, 11)
    path(marks, "M 272,269 C 277,245 310,239 328,255 C 343,266 353,243 379,240",
         "none", "#976c48", 5.5)
    path(marks, "M 307,337 C 349,361 385,330 400,281", "none", INK, 9)
    path(marks, "M 307,337 C 349,361 385,330 400,281", "none", "#6e818a", 4.7)

    antenna = layer(view, "part-antenna", "Alarm Mast")
    path(antenna, "M 291,249 L 283,223 L 285,201", "none", INK, 9)
    path(antenna, "M 291,249 L 283,223 L 285,201", "none", "#a2afb2", 4.5)
    path(antenna, "M 275,207 L 273,190 L 280,184 L 293,185 L 298,193 L 297,207 Z",
         RED, width=4)
    path(antenna, "M 280,189 L 285,187 L 289,191 L 290,201", "none", "#ffd4b7", 2.6)
    circle(antenna, (285, 211), 5.0, DEEP, INK, 2)

    flash = layer(view, "part-beacon-halo", "Alarm Flash")
    circle(flash, (285, 195), 15.0, "#ee7462", "none", 0)
    circle(flash, (285, 195), 7.5, "#ffe7ab", "none", 0)
    for x0, y0, x1, y1 in ((264,195,259,195),(306,195,311,195),
                           (285,174,285,169),(285,216,285,221)):
        path(flash, f"M {x0},{y0} L {x1},{y1}", "none", "#f6bb8a", 3)

    hatch = layer(view, "part-exhaust-hatch", "Rear Exhaust Hatch")
    path(hatch, "M 247,278 L 225,270 L 230,255 L 261,259 L 270,269 Z",
         "#748793", width=3.4)
    path(hatch, "M 234,263 L 258,265", "none", EDGE, 2.3)
    circle(hatch, (247, 277), 5.4, BRASS, INK, 2.0)

    heat = layer(view, "part-exhaust-glow", "Rear Exhaust Heat")
    for x in (246, 258, 270):
        path(heat, f"M {x},279 L {x+5},288", "none", "#ffbd65", 4.5)


def draw_light(view: ET.Element) -> None:
    beam = layer(view, "part-search-cone", "Soft Search Cone")
    path(beam, "M 463,251 L 664,196 L 664,339 L 463,268 Z",
         "#e3f7bb", "none", 0, **{"fill-opacity": "0.25"})
    path(beam, "M 466,253 L 665,242 L 665,298 L 465,265 Z",
         "#fff5c2", "none", 0, **{"fill-opacity": "0.12"})
    path(beam, "M 462,251 L 662,196 M 463,268 L 662,339", "none", "#d9f3ae", 1.7,
         **{"stroke-opacity": "0.60"})

    focused = layer(view, "part-search-cone-narrow", "Focused Search Cone")
    path(focused, "M 465,253 L 664,242 L 664,280 L 465,264 Z",
         "#f4ffd9", "none", 0, **{"fill-opacity": "0.45"})
    path(focused, "M 465,253 L 664,242 M 465,264 L 664,280",
         "none", "#f1ffd5", 2.6, **{"stroke-opacity": "0.85"})

    assembly = layer(view, "part-lamp", "Searchlight Assembly")
    lamp = layer(assembly, "lamp-housing", "Searchlight Housing")
    path(lamp, "M 384,231 L 408,218 L 443,226 L 456,238 L 456,276 L 444,290 "
         "L 407,294 L 385,283 L 376,263 Z", "#354651", width=5.7)
    path(lamp, "M 390,235 L 419,223 L 449,236 L 450,282 L 417,290 L 388,276 Z",
         "#81929c", width=4.3)
    path(lamp, "M 394,238 L 417,230 L 420,283 L 392,274 Z", "#5b6b77", width=3)
    path(lamp, "M 404,237 L 411,232 L 414,280 L 408,284 Z", RIM, "none", 0)
    path(lamp, "M 416,229 L 423,227 L 427,286 L 420,289 Z", INK, "none", 0)
    path(lamp, "M 383,257 L 361,254", "none", INK, 9)
    path(lamp, "M 383,257 L 363,254", "none", BRASS, 3.7)
    circle(lamp, (384, 258), 6.5, "#536672", INK, 2.5)
    for y in (234, 279):
        circle(lamp, (414, y), 3.4, BRASS, INK, 1.3)
    # Concentric heavy bevel makes the lamp a searchlight, not a soft eyeball.
    circle(lamp, (453, 258), 32, DEEP, INK, 4.8)
    circle(lamp, (453, 258), 27, "#c0c7b7", INK, 3.5)

    glass = layer(assembly, "lamp-glass", "Lensed Glass")
    circle(glass, (454, 258), 24.0, "#aabf9f", "#edf3d5", 3.2)
    circle(glass, (454, 258), 19.5, LAMP, "#709484", 2.6)
    circle(glass, (454, 258), 12.5, "#d1ecc8", "#a2c4ad", 2.0)
    path(glass, "M 446,249 Q 451,242 459,243", "none", "#ffffff", 4.1)
    path(glass, "M 463,267 Q 460,273 452,274", "none", "#7eafa0", 2.2)
    # Shutter screws are part of the lens face.
    for x, y in ((452, 226), (452, 289)):
        circle(glass, (x, y), 3.2, BRASS, INK, 1.3)

    alert = layer(view, "part-lamp-alert", "Alarm Iris")
    circle(alert, (454, 258), 9.5, "none", "#f28c6e", 3.2)
    path(alert, "M 446,251 L 462,265 M 463,250 L 445,265", "none", "#e95e55", 2.4)

    # Two leaf shutters stay on separate bones. They slide over the glass.
    upper = layer(view, "part-shutter-upper", "Upper Iris Shutter")
    path(upper, "M 432,216 L 448,216 L 453,222 L 460,216 L 476,216 "
         "L 475,239 L 432,239 Z", "#33424c", width=3.0)
    path(upper, "M 438,223 L 470,223", "none", "#83999f", 2.6)
    path(upper, "M 444,234 L 463,234", "none", BRASS, 1.8)
    lower = layer(view, "part-shutter-lower", "Lower Iris Shutter")
    path(lower, "M 433,277 L 475,277 L 476,300 L 460,300 L 453,294 "
         "L 448,300 L 432,300 Z", "#33424c", width=3.0)
    path(lower, "M 438,292 L 470,292", "none", "#83999f", 2.6)
    path(lower, "M 444,282 L 463,282", "none", BRASS, 1.8)


def build_svg() -> str:
    root = ET.Element(f"{{{SVG_NS}}}svg", {
        "width": f"{CANVAS[0]}mm", "height": f"{CANVAS[1]}mm",
        "viewBox": f"0 0 {CANVAS[0]} {CANVAS[1]}",
        "version": "1.1", "id": "searchlight-crawler-svg",
        f"{{{SOD_NS}}}docname": "searchlight_crawler.svg",
    })
    node(root, "defs", id="defs1")
    view = layer(root, "view-searchlight-crawler-side", VIEW)
    for leg, chain in LEG_POINTS.items():
        if not leg.startswith("far_"):
            continue
        for i, segment in enumerate(SEGMENTS):
            group = layer(view, f"part-{leg.replace('_', '-')}-{segment}",
                          f"{leg.replace('_', ' ').title()} / {segment.title()}")
            segment_art(group, chain[i], chain[i + 1], segment, False, "outer" in leg)

    draw_body(view)

    for leg, chain in LEG_POINTS.items():
        if not leg.startswith("near_"):
            continue
        for i, segment in enumerate(SEGMENTS):
            group = layer(view, f"part-{leg.replace('_', '-')}-{segment}",
                          f"{leg.replace('_', ' ').title()} / {segment.title()}")
            segment_art(group, chain[i], chain[i + 1], segment, True, "outer" in leg)

    draw_light(view)

    joints = layer(view, "joint-markers", "Rig Joints (show to edit)")
    joints.set("style", "display:none")
    for name, (_parent, x, y) in JOINTS.items():
        node(joints, "circle", id=f"joint-{name.replace('_', '-')}", cx=x, cy=y,
             r=2.0, fill="#ff3eb5", stroke=INK, **{"stroke-width": "0.7",
             "data-rig-joint": name})

    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode", xml_declaration=True) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Replace an edited SVG.")
    args = parser.parse_args()
    SVG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if SVG_PATH.exists() and not args.force:
        print(f"keep existing {SVG_PATH.relative_to(ROOT)}")
        return
    SVG_PATH.write_text(build_svg(), encoding="utf8")
    print(f"wrote {SVG_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
