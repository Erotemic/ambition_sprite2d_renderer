#!/usr/bin/env python3
"""Create the first editable SVG drawing of the Shock Warden.

    uv run python scripts/svg_art/shock_warden_art.py

The existing SVG is the art source. This command will not replace artist edits.
Use --force only to replace the SVG with the generated first draft.
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NAME = "shock_warden"
VIEW = "Shock Warden - Side"
SVG = ROOT / "ambition_sprite2d_renderer/data/characters/shock_warden/shock_warden.svg"
GROUND_Y = 476.0
CENTER_X = 350.0

# Initial rest-pose joints. The rig builder reads the marker coordinates from
# the SVG so later art edits can move joints without changing this script.
JOINTS = {
    "hips": (None, 348, 375),
    "torso": ("hips", 344, 304),
    "head": ("torso", 338, 231),
    "far_thigh": ("hips", 376, 372),
    "far_shin": ("far_thigh", 412, 417),
    "far_boot": ("far_shin", 415, 460),
    "near_thigh": ("hips", 311, 370),
    "near_shin": ("near_thigh", 272, 419),
    "near_boot": ("near_shin", 260, 459),
    "shield_upper": ("torso", 397, 289),
    "shield_forearm": ("shield_upper", 422, 323),
    "shield": ("shield_forearm", 455, 340),
    "baton_upper": ("torso", 289, 291),
    "baton_forearm": ("baton_upper", 250, 340),
    "baton_hand": ("baton_forearm", 222, 357),
    "baton": ("baton_hand", 219, 356),
}

# (one or more SVG group IDs, part name, bone, z, opacity channel)
# Parts on the same bone use one raster. Inkscape keeps their sublayers editable.
PARTS = [
    (("far-thigh",), "far_thigh", "far_thigh", 10, None),
    (("far-shin",), "far_shin", "far_shin", 11, None),
    (("far-boot",), "far_boot", "far_boot", 12, None),
    (("coat-tails", "hip-belt"), "coat_tails", "hips", 16, None),
    (("shield-upper",), "shield_upper", "shield_upper", 18, None),
    (("shield-forearm",), "shield_forearm", "shield_forearm", 19, None),
    (("torso-armor", "torso-details"), "torso", "torso", 30, None),
    (("near-thigh",), "near_thigh", "near_thigh", 34, None),
    (("near-shin",), "near_shin", "near_shin", 35, None),
    (("near-boot",), "near_boot", "near_boot", 36, None),
    (("head", "helmet", "face"), "head", "head", 40, None),
    (("baton-upper", "insignia"), "baton_upper", "baton_upper", 50, None),
    (("baton-forearm",), "baton_forearm", "baton_forearm", 51, None),
    (("baton-hand",), "baton_hand", "baton_hand", 52, None),
    (("baton-weapon",), "baton", "baton", 53, None),
    (("baton-electric",), "baton_electric", "baton", 54, "baton_charge"),
    (("shield-grip",), "shield_grip", "shield", 70, None),
    (("shield-main", "shield-emblem", "shield-viewport"), "shield", "shield", 71, None),
    (("shield-electric",), "shield_electric", "shield", 72, "shield_charge"),
    (("shield-impact",), "shield_impact", "shield", 73, "shield_impact"),
]

INK = "#181b21"
DARK = "#262a34"
COAT = "#32333e"
COAT_HI = "#464651"
ARMOR = "#59635b"
ARMOR_HI = "#798277"
GREEN = "#758774"
RED = "#a83439"
STEEL = "#9ba4a5"
BLUE = "#61bdff"
LIGHT = "#c9ecff"


def path(d: str, fill: str, stroke: str = INK, sw: float = 5, extra: str = "") -> str:
    return (f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
            f'stroke-linejoin="round" stroke-linecap="round" {extra}/>')


def ellipse(x: float, y: float, rx: float, ry: float, fill: str, sw: float = 4) -> str:
    return (f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" '
            f'fill="{fill}" stroke="{INK}" stroke-width="{sw}"/>')


def circle(x: float, y: float, r: float, fill: str, sw: float = 3) -> str:
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{INK}" stroke-width="{sw}"/>'


def group(gid: str, label: str, *elements: str) -> str:
    return (f'    <g id="{gid}" inkscape:label="{label}">\n      '
            + "\n      ".join(elements) + "\n    </g>")


def gear(cx: float, cy: float, radius: float, teeth: int = 10) -> str:
    points = []
    for i in range(teeth * 4):
        a = 2 * math.pi * i / (teeth * 4) - math.pi / 2
        r = radius * (1 if i % 4 in (1, 2) else 0.79)
        points.append(f"{cx + r * math.cos(a):.2f},{cy + r * math.sin(a):.2f}")
    return "M " + " L ".join(points) + " Z"


def build_svg() -> str:
    layers = []
    layers.append(group("far-thigh", "Far Thigh",
        path("M 366,368 Q 392,367 409,393 L 424,409 Q 411,427 396,431 L 373,402 Z", "#373b44", sw=5),
        path("M 391,390 L 411,412", "none", "#565c65", 6)))
    layers.append(group("far-shin", "Far Shin",
        path("M 396,415 Q 413,411 428,423 L 433,461 L 404,463 L 397,430 Z", "#3b414b"),
        path("M 421,430 L 422,459", "none", ARMOR, 5)))
    layers.append(group("far-boot", "Far Boot",
        path("M 399,449 L 430,448 L 444,467 Q 448,476 439,478 L 392,478 Q 386,472 390,465 Z", "#272933"),
        path("M 397,466 L 438,466", "none", "#666a6f", 4)))

    layers.append(group("coat-tails", "Coat Tails",
        path("M 273,348 L 404,356 L 431,453 L 366,444 L 333,461 L 307,436 L 260,446 L 240,428 L 258,379 Z", COAT),
        path("M 260,434 L 304,425 M 333,449 L 347,394 M 372,437 L 390,385", "none", COAT_HI, 4)))
    layers.append(group("hip-belt", "Belt and Equipment",
        path("M 273,372 Q 338,388 411,363 L 418,388 Q 347,411 274,390 Z", "#24262e"),
        path("M 342,384 L 366,381 L 369,402 L 343,405 Z", STEEL),
        path("M 348,389 L 361,387 L 361,397 L 350,399 Z", "#4e5456", sw=2),
        path("M 264,377 L 296,381 L 290,414 L 265,409 Z", "#41434d"),
        path("M 382,378 L 410,370 L 419,406 L 393,414 Z", "#41434d")))

    layers.append(group("shield-upper", "Shield Arm - Upper",
        path("M 385,281 Q 414,281 429,298 L 438,316 L 414,334 L 392,313 Z", DARK),
        path("M 393,293 L 418,314", "none", ARMOR, 8)))
    layers.append(group("shield-forearm", "Shield Arm - Lower",
        path("M 416,308 Q 430,303 449,318 L 471,342 L 455,355 L 422,336 Z", "#454a50"),
        path("M 431,317 L 454,340", "none", "#758079", 8)))

    layers.append(group("torso-armor", "Torso Armor",
        path("M 296,272 Q 310,246 350,251 Q 402,250 417,291 L 413,371 Q 384,397 333,392 Q 274,398 261,361 L 268,298 Q 269,285 296,272 Z", COAT),
        path("M 292,286 L 320,277 Q 329,329 318,373 L 286,361 Z", ARMOR),
        path("M 366,276 L 397,288 L 401,363 L 369,376 Q 375,322 366,276 Z", ARMOR),
        path("M 327,276 L 360,274 L 366,380 L 326,377 Z", "#343a40"),
        path("M 329,300 L 356,300 M 328,321 L 357,321 M 329,342 L 358,342", "none", "#78816f", 4),
        path("M 269,280 Q 289,258 312,271 L 312,310 Q 276,309 259,299 Z", "#424751"),
        path("M 376,270 Q 404,266 430,283 L 422,307 L 386,313 Z", "#3b3e46")))
    layers.append(group("torso-details", "Torso Fasteners",
        path("M 321,283 L 320,380 M 366,283 L 366,378", "none", INK, 3),
        circle(336,291,3,"#cad0c9",1), circle(341,363,3,"#cad0c9",1),
        path("M 277,347 L 309,352 M 382,350 L 405,345", "none", "#a0a697", 3)))

    layers.append(group("near-thigh", "Near Thigh",
        path("M 293,362 Q 314,361 324,382 L 301,424 L 265,415 Q 269,387 293,362 Z", COAT),
        path("M 302,381 L 285,409", "none", COAT_HI, 5)))
    layers.append(group("near-shin", "Near Shin",
        path("M 259,405 L 286,410 L 285,461 L 254,468 L 243,452 Z", "#4f5058"),
        path("M 266,417 L 262,457", "none", "#686974", 5)))
    layers.append(group("near-boot", "Near Boot",
        path("M 250,449 L 284,450 L 294,465 L 298,478 L 216,478 Q 208,472 219,465 L 244,460 Z", "#292a32"),
        path("M 220,467 L 290,467", "none", "#6c7071", 4)))

    layers.append(group("head", "Face and Mask",
        path("M 299,200 Q 302,182 321,180 L 368,187 L 392,205 L 386,258 Q 371,280 332,276 L 303,254 Z", "#33363e"),
        path("M 307,237 L 384,229 L 370,271 L 318,264 Z", "#c9d0c9"),
        path("M 313,247 L 370,241 L 370,261 L 320,261 Z", "#1f242d"),
        path("M 320,248 L 327,262 M 331,246 L 336,262 M 343,244 L 346,261 M 355,242 L 357,261", "none", "#7b8786", 4)))
    layers.append(group("face", "Visor and Eyes",
        path("M 301,214 L 382,207 L 381,234 L 305,240 Z", "#191f29"),
        path("M 309,229 L 348,224 L 350,230 L 312,236 Z", "#eff3ed", "#262a33", 2),
        path("M 347,224 L 373,220 L 366,229 L 352,231 Z", "#f0e8df", "#262a33", 2),
        path("M 333,227 L 337,231 M 358,224 L 361,228", "none", RED, 3),
        path("M 308,215 L 381,209", "none", "#5e6767", 3)))
    layers.append(group("helmet", "Helmet",
        path("M 293,212 L 305,178 Q 330,164 363,171 L 386,189 L 384,217 L 287,223 Z", DARK),
        path("M 291,215 Q 338,210 392,210 L 399,221 L 290,230 Z", "#252931"),
        path("M 311,183 Q 344,176 369,188", "none", "#5c6066", 5),
        path("M 342,180 L 354,180 L 353,194 L 342,194 Z", ARMOR_HI, sw=2)))

    layers.append(group("baton-upper", "Baton Arm - Upper",
        path("M 288,281 Q 272,277 258,291 L 238,334 L 264,354 L 301,313 Z", COAT),
        path("M 256,312 L 271,292", "none", COAT_HI, 7),
        path("M 242,325 L 265,345", "none", "#5b6065", 7)))
    layers.append(group("insignia", "Fictional Unit Badge",
        path("M 270,289 L 299,301 L 282,328 L 255,316 Z", RED, sw=3),
        ellipse(276,308,9,8,"#e9e7dd",2),
        path(gear(276,308,6,8), "#23252b", "#23252b", 1),
        circle(276,308,2,"#e9e7dd",1)))
    layers.append(group("baton-forearm", "Baton Arm - Forearm",
        path("M 246,325 L 265,344 L 242,363 L 221,352 Z", ARMOR),
        path("M 239,335 L 256,345", "none", "#a0ad9c", 6)))
    layers.append(group("baton-hand", "Baton Hand",
        path("M 230,341 Q 243,343 246,356 Q 247,369 228,376 L 215,369 L 216,352 Z", GREEN),
        path("M 224,351 L 235,354 M 220,358 L 232,362", "none", "#485c4d", 3)))
    layers.append(group("baton-weapon", "Baton Weapon",
        path("M 215,352 L 120,344", "none", "#1b2530", 19),
        path("M 211,351 L 129,343", "none", "#6c7881", 10),
        path("M 145,339 L 143,352 M 157,342 L 155,354 M 189,347 L 187,358", "none", INK, 5),
        circle(118,343,9,"#93a5b0",3),
        path("M 192,341 L 204,346 L 202,358 L 190,358 Z", "#3a4048")))
    layers.append(group("baton-electric", "Baton Electrical Arc",
        path("M 121,326 L 139,337 L 148,327 L 166,339 L 179,333 L 190,340 L 205,339", "none", BLUE, 5),
        path("M 114,357 L 132,350 L 140,361 L 164,353 L 179,367 L 195,357", "none", "#addfff", 4),
        path("M 142,322 L 148,312 L 156,324", "none", BLUE, 3)))

    layers.append(group("shield-grip", "Shield Handle",
        path("M 445,329 L 480,320 L 489,355 L 454,359 Z", "#353c41", sw=5),
        path("M 457,336 L 479,331", "none", ARMOR_HI, 6)))
    layers.append(group("shield-main", "Shield Steel and Frame",
        path("M 450,184 Q 450,174 462,174 L 520,180 Q 534,180 534,193 L 537,457 Q 537,466 525,469 L 456,468 Q 447,464 447,452 Z", "#717d7e", sw=7),
        path("M 461,190 L 519,193 L 521,454 L 461,453 Z", "#2c333d", sw=4),
        path("M 467,246 L 515,250 L 515,433 L 469,434 Z", "#4e555b", sw=3),
        path("M 462,198 L 519,201 M 461,442 L 521,443", "none", "#b1baba", 5),
        path("M 452,188 L 452,459", "none", "#b4c4c6", 4),
        circle(461,205,3,"#bac0bd",1), circle(521,208,3,"#bac0bd",1),
        circle(461,446,3,"#bac0bd",1), circle(521,449,3,"#bac0bd",1)))
    layers.append(group("shield-viewport", "Shield Viewing Slit",
        path("M 468,218 L 513,222 L 512,240 L 469,237 Z", "#141e2d", sw=3),
        path("M 473,223 L 508,226 L 508,232 L 473,231 Z", "#b3dded", "none", 0)))
    layers.append(group("shield-emblem", "Shield Gear Badge",
        path("M 470,304 L 512,302 L 513,367 L 470,366 Z", "#8b9793", sw=3),
        path(gear(491,334,22,10), "#2d343a", "#2d343a", 2),
        circle(491,334,9,"#8b9793",2)))
    layers.append(group("shield-electric", "Shield Electrical Arcs",
        path("M 445,189 L 440,177 L 451,171 L 448,162 M 530,194 L 541,202 L 535,217 L 547,229 L 537,245", "none", BLUE, 5),
        path("M 447,260 L 436,270 L 449,283 L 440,303 L 450,317 M 538,328 L 546,343 L 533,363 L 544,376 L 535,398", "none", "#a2e8ff", 4),
        path("M 448,420 L 440,431 L 452,445 L 448,461 L 461,478 M 517,473 L 531,477 L 539,467", "none", BLUE, 4),
        path("M 451,186 L 448,453 M 534,190 L 537,454", "none", "#4caaff", 3, 'opacity="0.7"')))
    layers.append(group("shield-impact", "Shield Bash Impact Flash",
        path("M 539,254 L 561,241 L 552,269 L 575,277 L 552,287 L 566,313 L 539,306", "none", LIGHT, 7),
        path("M 539,374 L 562,357 L 556,388 L 571,402", "none", BLUE, 5)))

    markers = []
    for name, (_, x, y) in JOINTS.items():
        markers.append(f'<circle id="joint-{name}" data-rig-joint="{name}" cx="{x}" cy="{y}" r="3" fill="#ff3eb5"/>')
    layers.append(f'    <g id="joint-markers" inkscape:label="Joints (hidden)" style="display:none">' + "".join(markers) + "</g>")
    return ('''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
 xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
 width="760mm" height="560mm" viewBox="0 0 760 560" version="1.1">
 <g id="view-shock-warden-side" inkscape:groupmode="layer" inkscape:label="Shock Warden - Side">
''' + "\n".join(layers) + "\n </g>\n</svg>\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Replace edited SVG art.")
    args = parser.parse_args()
    SVG.parent.mkdir(parents=True, exist_ok=True)
    if SVG.exists() and not args.force:
        print(f"kept existing {SVG.relative_to(ROOT)}")
        return
    SVG.write_text(build_svg(), encoding="utf8")
    print(f"wrote {SVG.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
