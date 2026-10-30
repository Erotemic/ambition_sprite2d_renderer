#!/usr/bin/env python3
"""Create the first editable SVG drawing of the Shock Warden.

    uv run python scripts/svg_art/shock_warden_art.py

The existing SVG is the art source. This command will not replace artist edits.
Run ``scripts/build_shock_warden_rig.py`` after a source edit or regeneration
to update the skeleton and the SVG catalog. Use --force only to replace the
SVG with the programmatic drawing.
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
    "head": ("torso", 340, 232),
    "far_thigh": ("hips", 376, 372),
    "far_shin": ("far_thigh", 412, 417),
    "far_boot": ("far_shin", 415, 460),
    "near_thigh": ("hips", 311, 370),
    "near_shin": ("near_thigh", 272, 419),
    "near_boot": ("near_shin", 260, 459),
    "shield_upper": ("torso", 395, 290),
    "shield_forearm": ("shield_upper", 424, 323),
    "shield": ("shield_forearm", 451, 343),
    "baton_upper": ("torso", 288, 290),
    "baton_forearm": ("baton_upper", 250, 338),
    "baton_hand": ("baton_forearm", 222, 356),
    "baton": ("baton_hand", 216, 358),
}

# (one or more SVG group IDs, part name, bone, z, opacity channel)
# Parts on the same bone use one raster. Inkscape keeps their sublayers editable.
PARTS = [
    # The canvas-right leg is in front of the rear coat tails. Keep the belt
    # in front of its hip joint so the leg connects below the uniform.
    (("coat-tails",), "coat_tails", "hips", 16, None),
    (("far-thigh",), "far_thigh", "far_thigh", 18, None),
    (("far-shin",), "far_shin", "far_shin", 19, None),
    (("far-boot",), "far_boot", "far_boot", 20, None),
    (("hip-belt",), "hip_belt", "hips", 24, None),
    (("shield-upper",), "shield_upper", "shield_upper", 37, None),
    (("shield-forearm",), "shield_forearm", "shield_forearm", 38, None),
    (("torso-armor", "torso-details"), "torso", "torso", 30, None),
    (("near-thigh",), "near_thigh", "near_thigh", 34, None),
    (("near-shin",), "near_shin", "near_shin", 35, None),
    (("near-boot",), "near_boot", "near_boot", 36, None),
    (("head", "helmet", "face"), "head", "head", 43, None),
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
        path("M 364,365 Q 391,362 407,388 Q 419,401 421,416 L 398,429 Q 382,413 371,400 Z", "#343b43", sw=5),
        path("M 381,377 Q 403,393 408,414", "none", "#66716d", 5)))
    layers.append(group("far-shin", "Far Shin",
        path("M 399,414 Q 412,405 427,422 L 430,452 L 419,465 L 401,455 L 397,430 Z", "#414b51"),
        path("M 415,425 L 418,451", "none", ARMOR, 5),
        circle(412,417,7,"#65706c",2)))
    layers.append(group("far-boot", "Far Boot",
        path("M 399,452 L 430,449 L 454,466 Q 460,471 455,479 L 397,479 L 390,472 Z", "#262e36"),
        path("M 401,466 L 448,466 M 391,474 L 455,474", "none", "#6c7877", 3)))
    layers.append(group("coat-tails", "Layered Coat Tails",
        path("M 275,349 Q 338,370 404,350 L 425,404 L 416,453 L 365,444 L 335,463 L 304,438 L 252,452 L 236,428 Z", COAT),
        path("M 256,441 L 284,369 L 308,439 M 334,451 L 347,383 M 377,437 L 398,371", "none", COAT_HI, 4),
        path("M 257,436 L 293,444 M 365,443 L 412,447", "none", INK, 3)))
    layers.append(group("hip-belt", "Angled Belt and Equipment",
        path("M 265,368 Q 333,389 413,360 L 420,387 Q 342,415 273,390 Z", "#222830"),
        path("M 342,384 L 369,380 L 372,401 L 342,405 Z", STEEL),
        path("M 349,390 L 363,387 L 363,397 L 349,399 Z", "#46505a", sw=2),
        path("M 271,381 L 297,383 L 292,410 L 267,407 Z", "#4b4c50"),
        path("M 389,375 L 412,368 L 421,406 L 396,411 Z", "#45454c"),
        path("M 281,385 L 286,404 M 403,377 L 407,399", "none", "#7b7978", 3)))
    layers.append(group("shield-upper", "Shield Arm - Upper Sleeve",
        path("M 386,280 Q 400,271 414,285 L 432,307 L 435,321 L 416,335 L 397,314 L 385,298 Z", DARK),
        path("M 399,290 L 418,315", "none", ARMOR_HI, 7),
        path("M 405,302 L 427,317", "none", INK, 3)))
    layers.append(group("shield-forearm", "Shield Arm - Braced Forearm",
        path("M 416,311 Q 432,305 441,322 L 462,344 L 449,360 L 420,342 Z", "#56635e"),
        path("M 426,320 L 449,343", "none", "#a0aea3", 7),
        path("M 438,321 L 454,337", "none", INK, 3),
        ellipse(425,323,8,9,"#374149",3)))
    layers.append(group("torso-armor", "Three Quarter Torso and Armor",
        path("M 284,277 Q 309,250 352,250 Q 397,247 422,282 L 420,367 Q 391,392 344,392 Q 298,393 263,362 L 268,306 Q 271,286 284,277 Z", COAT),
        path("M 270,290 L 303,269 L 329,281 L 326,374 L 269,359 Z", "#424b4e"),
        path("M 331,270 L 375,268 L 382,371 L 328,378 Z", "#343a40"),
        path("M 379,278 L 411,290 L 410,359 L 384,374 Z", ARMOR),
        path("M 288,284 L 314,280 L 315,371 L 284,355 Z", ARMOR),
        path("M 327,280 L 376,278 L 380,374 L 329,379 Z", "#252c34"),
        path("M 270,283 Q 284,263 310,270 L 319,293 L 304,308 L 266,305 Z", "#4e5559"),
        path("M 377,271 Q 410,264 437,288 L 428,310 L 395,315 L 382,296 Z", "#424c50"),
        path("M 381,285 L 422,295", "none", "#778478", 5)))
    layers.append(group("torso-details", "Three Quarter Torso Fasteners",
        path("M 327,282 L 326,373 M 378,278 L 382,371", "none", INK, 3),
        path("M 337,299 L 365,298 M 335,320 L 366,320 M 335,342 L 369,342", "none", "#87978a", 4),
        path("M 278,348 L 304,354 M 392,350 L 408,345", "none", "#a8aea6", 3),
        circle(341,286,3,"#d2d7d1",1), circle(347,363,3,"#d2d7d1",1),
        path("M 403,290 L 409,297", "none", "#b4b3a2", 3)))
    layers.append(group("near-thigh", "Near Thigh and Knee",
        path("M 301,359 Q 326,362 323,385 L 290,426 L 261,414 Q 271,377 301,359 Z", COAT),
        path("M 302,382 L 283,408", "none", "#646570", 6),
        ellipse(274,413,12,10,"#4f5758",3)))
    layers.append(group("near-shin", "Near Shin Plate",
        path("M 262,407 Q 278,411 288,420 L 281,463 L 252,469 L 241,450 Z", "#4e575e"),
        path("M 265,422 L 258,457", "none", "#8e9690", 5),
        path("M 245,447 L 276,458", "none", "#363d45", 4)))
    layers.append(group("near-boot", "Heavy Near Boot",
        path("M 251,449 L 284,450 L 291,464 L 303,475 Q 302,480 293,480 L 218,480 Q 209,477 215,468 L 244,460 Z", "#292f37"),
        path("M 216,471 L 294,471 M 252,455 L 276,455", "none", "#7b8583", 4),
        path("M 216,479 L 293,479", "none", INK, 4)))
    layers.append(group("head", "Head - Side Mask and Jaw",
        path("M 308,204 Q 311,182 334,183 L 379,193 L 404,219 L 404,257 Q 389,277 361,283 L 324,267 L 310,242 Z", "#343941"),
        path("M 326,223 L 354,221 L 355,274 L 325,259 Z", "#4c5459"),
        path("M 355,226 L 401,226 L 398,257 L 382,272 L 355,269 Z", "#acb7b3"),
        path("M 360,244 L 394,242 L 392,260 L 361,262 Z", "#202832"),
        path("M 364,246 L 364,262 M 373,246 L 375,261 M 382,245 L 386,259", "none", "#9baaa8", 4),
        path("M 346,254 L 360,270 L 383,272", "none", INK, 4)))
    layers.append(group("face", "Directional Visor and Red Eyes",
        path("M 326,216 L 404,220 L 406,240 L 340,239 Z", "#1a212c"),
        path("M 342,229 L 369,229 L 372,235 L 345,235 Z", "#dce1dc", "#20262b", 2),
        path("M 376,228 L 397,229 L 393,236 L 377,235 Z", "#f0eae1", "#20262b", 2),
        path("M 366,232 L 370,236 M 389,231 L 391,236", "none", RED, 3),
        path("M 330,218 L 402,224", "none", "#667275", 3)))
    layers.append(group("helmet", "Sloped Helmet and Forward Brim",
        path("M 305,210 L 313,185 Q 329,168 358,171 Q 389,175 399,200 L 397,220 L 301,221 Z", DARK),
        path("M 301,214 L 400,214 L 416,225 Q 412,233 399,232 L 299,231 Z", "#202831"),
        path("M 317,187 Q 342,179 370,191 L 387,200", "none", "#667475", 5),
        path("M 344,182 L 358,185 L 357,200 L 344,198 Z", ARMOR_HI, sw=2),
        path("M 308,219 L 405,224", "none", "#6c7273", 3)))
    layers.append(group("baton-upper", "Baton Arm - Shoulder and Upper Sleeve",
        path("M 285,281 Q 267,277 257,293 L 237,333 Q 235,341 248,351 L 266,349 L 298,311 L 304,297 Z", COAT),
        path("M 270,299 L 251,331", "none", "#717a75", 7),
        path("M 242,325 L 266,345", "none", "#5e636b", 6),
        path("M 261,291 Q 276,281 295,294", "none", INK, 3)))
    layers.append(group("insignia", "Fictional Unit Badge",
        path("M 263,294 L 298,300 L 288,327 L 253,317 Z", RED, sw=3),
        ellipse(276,309,10,9,"#ece8db",2),
        path(gear(276,309,7,8), "#242a31", "#242a31", 1),
        circle(276,309,2,"#e9e7dd",1)))
    layers.append(group("baton-forearm", "Baton Arm - Forearm Plate",
        path("M 246,324 L 265,342 L 241,366 L 218,349 Z", ARMOR),
        path("M 239,334 L 257,348", "none", "#b0b7a7", 6),
        path("M 224,349 L 236,360", "none", INK, 3)))
    layers.append(group("baton-hand", "Gripping Baton Hand",
        path("M 230,340 Q 245,345 245,359 Q 241,374 224,377 L 208,364 L 214,347 Z", GREEN),
        path("M 217,350 L 231,353 M 213,360 L 225,364", "none", "#455e4e", 3)))
    layers.append(group("baton-weapon", "Steel Baton, Grip and Tip",
        # A thick shaft with a pale steel face, so it reads at game scale.
        path("M 214,359 L 124,342", "none", "#141a20", 24),
        path("M 208,357 L 129,342", "none", "#aebfc4", 13),
        path("M 204,353 L 133,339", "none", "#e4eff1", 4),
        # The ribbed black grip and its red band of the unit.
        path("M 214,360 L 186,355", "none", "#262c33", 16),
        path("M 207,352 L 205,364 M 199,351 L 197,363 M 191,349 L 189,361", "none", "#4a535c", 3),
        path("M 183,348 L 180,361", "none", RED, 6),
        # The tip: a bright steel cap with the contacts.
        circle(126,342,11,"#d8e6e8",4),
        circle(126,342,4,BLUE,2)))
    layers.append(group("baton-electric", "Baton Electrical Arc",
        path("M 116,330 L 124,334 L 120,322 L 131,328 L 134,318", "none", BLUE, 4),
        path("M 117,353 L 126,350 L 121,361 L 133,357", "none", LIGHT, 3)))
    layers.append(group("shield-grip", "Arm and Shield Bracket",
        path("M 438,329 Q 451,321 463,326 L 473,340 L 467,357 L 452,363 L 437,352 Z", "#6d7f73", sw=5),
        path("M 447,337 L 469,337 M 450,345 L 470,345", "none", "#a8b4ac", 5),
        path("M 456,328 L 461,350", "none", INK, 3)))
    layers.append(group("shield-main", "Perspective Shield: Return and Front Plate",
        # The rim is pale and thick, so the shield's edge reads at game scale.
        path("M 456,180 Q 456,174 465,175 L 527,190 Q 535,191 537,201 L 548,463 Q 549,475 536,478 L 456,462 Q 449,459 449,448 Z", "#c3d0d2", sw=8),
        path("M 456,187 L 478,200 L 479,457 L 456,455 Z", "#4d5e66", sw=3),
        path("M 477,199 L 527,209 L 539,464 L 479,453 Z", "#34464f", sw=4),
        path("M 487,251 L 520,255 L 530,424 L 487,419 Z", "#4f6268", sw=3),
        # Hazard stripes along the foot of the face.
        path("M 482,430 L 536,440 L 538,458 L 482,449 Z", "#d9b23c", sw=3),
        path("M 490,432 L 484,448 M 505,435 L 499,451 M 520,438 L 514,454 M 535,441 L 529,456", "none", "#1a1f26", 5),
        path("M 459,194 L 525,206", "none", "#eef4f2", 5),
        path("M 461,196 L 466,447", "none", "#d6e2e3", 4),
        path("M 532,211 L 544,463", "none", "#e3ecea", 4),
        circle(467,207,3,"#eef2ee",1), circle(519,214,3,"#eef2ee",1),
        circle(466,439,3,"#eef2ee",1), circle(529,454,3,"#eef2ee",1)))
    layers.append(group("shield-viewport", "Perspective Viewing Slit",
        path("M 486,221 L 525,229 L 527,248 L 486,241 Z", "#13212e", sw=3),
        path("M 491,229 L 520,234 L 522,241 L 491,237 Z", "#e2fbff", "none", 0)))
    layers.append(group("shield-emblem", "Shield Gear Plate",
        # The faction's cog, large, white on red: the mark reads first.
        path("M 485,293 L 525,297 L 529,377 L 487,372 Z", RED, sw=4),
        circle(507,335,19,"#ece8db",3),
        path(gear(507,335,15,8), "#1d2228", "#1d2228", 2),
        circle(507,335,5,"#ece8db",2)))
    layers.append(group("shield-electric", "Shield Electrical Rim",
        path("M 455,188 L 445,178 L 458,169 L 453,160 M 528,198 L 544,204 L 539,219 L 552,229 L 540,245", "none", BLUE, 5),
        path("M 451,272 L 442,285 L 454,297 L 444,314 L 455,326 M 545,327 L 556,344 L 545,360 L 559,377 L 547,398", "none", LIGHT, 4),
        path("M 455,417 L 444,431 L 458,445 L 454,463 L 468,480 M 534,473 L 544,481 L 553,465", "none", BLUE, 4),
        path("M 457,191 L 455,453 M 532,207 L 545,459", "none", "#4caaff", 3, 'opacity="0.7"')))
    layers.append(group("shield-impact", "Shield Bash Impact Flash",
        path("M 545,257 L 567,245 L 558,272 L 578,283 L 558,292 L 571,314 L 546,305", "none", LIGHT, 7),
        path("M 551,372 L 569,357 L 562,388 L 581,404", "none", BLUE, 5)))
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
