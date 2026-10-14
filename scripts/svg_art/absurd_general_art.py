#!/usr/bin/env python3
"""Draw the General (``absurd_general``): a first draft of his SVG.

    uv run python scripts/svg_art/absurd_general_art.py
    uv run python scripts/build_absurd_general_rig.py

Writes ``data/characters/absurd_general/absurd_general.svg``.

Jon, 2026-10-13, with a picture of a cartoon general: "I'm going for a
general specific sort of vibe (although again, we are not copying the
character, this is just inspiration)". What is taken from the picture is the
SHAPE of the joke: a coat like a box on two legs like sticks, a nose like a
bulb, teeth shut tight, arms akimbo. What is his own: the olive and gold of
the General this game had, a red sash, a swagger stick under his arm, and his
hat. The first draft had the tall leaning hat of the picture; Jon: "No, redo
the general hat, Just a normal officer hat". So it is a peaked service cap.

He is drawn at three quarters, facing right, as the toon cast is. Each part
is a layer with a ``data-rig-part`` name. ``JOINTS`` says where each part
turns; the rig builder reads it from this module. The SVG owns the art after
this script has run once.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "ambition_sprite2d_renderer" / "data" / "characters" / "absurd_general" / "absurd_general.svg"
VIEW = "General - Three Quarter Right"

O = "#181512"  # the ink
COAT, COAT_DARK, COAT_LIGHT = "#4d7a45", "#2f5330", "#6a9a5c"
TRIM = "#1d3421"
HAT, HAT_DARK, HAT_LIGHT = "#2f5c38", "#1f4429", "#4f8456"
GOLD, GOLD_DARK = "#ffd34f", "#b77814"
SKIN, SKIN_SHADE, NOSE = "#e0a27f", "#b8725f", "#e9a48a"
RED = "#b3312c"
SHOE = "#201d17"
WHITE = "#fff0db"
BLUE = "#3f6fb5"

#: The ground, in SVG units. The frame of the rig puts it at its ground line.
GROUND_Y = 600.0
#: Where each bone turns (SVG units): ``bone: (parent, x, y)``, parents first.
JOINTS: Dict[str, Tuple[str, float, float]] = {
    "body": ("", 322.0, 528.0),
    "torso": ("body", 322.0, 528.0),
    "head": ("torso", 332.0, 318.0),
    "hat": ("head", 334.0, 212.0),
    "near_arm_upper": ("torso", 242.0, 346.0),
    "near_arm_lower": ("near_arm_upper", 192.0, 420.0),
    "far_arm_upper": ("torso", 414.0, 346.0),
    "far_arm_lower": ("far_arm_upper", 482.0, 416.0),
    "near_leg": ("body", 344.0, 524.0),
    "near_foot": ("near_leg", 344.0, 588.0),
    "far_leg": ("body", 300.0, 524.0),
    "far_foot": ("far_leg", 300.0, 588.0),
}


def path(d: str, fill: str, stroke: str = "", width: float = 0.0) -> str:
    out = f'<path d="{d}" fill="{fill}"'
    if stroke:
        out += f' stroke="{stroke}" stroke-width="{width:g}" stroke-linejoin="round"'
    return out + "/>"


def line(d: str, stroke: str, width: float) -> str:
    return f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="{width:g}" stroke-linecap="round" stroke-linejoin="round"/>'


def tube(a: Tuple[float, float], b: Tuple[float, float], width: float, fill: str) -> List[str]:
    """A limb from ``a`` to ``b``: a thick line with round ends, in ink and then in ``fill``."""
    d = f"M{a[0]:g} {a[1]:g} L{b[0]:g} {b[1]:g}"
    return [line(d, O, width + 13), line(d, fill, width)]


def star(cx: float, cy: float, r: float, turn: float = -90.0, points: int = 5) -> str:
    pts = []
    for i in range(points * 2):
        rad = r if i % 2 == 0 else r * (0.42 if points == 5 else 0.6)
        ang = math.radians(turn + 180.0 / points * i)
        pts.append(f"{cx + rad * math.cos(ang):.1f} {cy + rad * math.sin(ang):.1f}")
    return "M" + " L".join(pts) + " Z"


def circle(cx: float, cy: float, r: float, fill: str, stroke: str = "", width: float = 0.0) -> str:
    out = f'<circle cx="{cx:g}" cy="{cy:g}" r="{r:g}" fill="{fill}"'
    if stroke:
        out += f' stroke="{stroke}" stroke-width="{width:g}"'
    return out + "/>"


def ellipse(cx: float, cy: float, rx: float, ry: float, fill: str, stroke: str = "", width: float = 0.0) -> str:
    out = f'<ellipse cx="{cx:g}" cy="{cy:g}" rx="{rx:g}" ry="{ry:g}" fill="{fill}"'
    if stroke:
        out += f' stroke="{stroke}" stroke-width="{width:g}"'
    return out + "/>"


def medal(x: float, y: float, ribbon: str, kind: str) -> List[str]:
    """A medal that hangs from a ribbon. ``(x, y)`` is the top of the ribbon."""
    out = [path(f"M{x - 7:g} {y:g} L{x + 7:g} {y:g} L{x + 5:g} {y + 16:g} L{x:g} {y + 20:g} L{x - 5:g} {y + 16:g} Z", ribbon, O, 2.5)]
    cy = y + 28
    if kind == "disc":
        out.append(circle(x, cy, 8, GOLD, GOLD_DARK, 3))
    elif kind == "star":
        out.append(path(star(x, cy, 10), GOLD, GOLD_DARK, 2.5))
    else:
        out.append(path(f"M{x - 3:g} {cy - 9:g} h6 v6 h6 v6 h-6 v6 h-6 v-6 h-6 v-6 h6 Z", GOLD, GOLD_DARK, 2.5))
    return out


def leg(x: float, fill: str, stripe: str) -> List[str]:
    """One leg like a stick, from the hem of the coat to the ankle."""
    return [
        path(f"M{x - 9:g} 512 L{x + 9:g} 512 L{x + 7:g} 590 L{x - 7:g} 590 Z", fill, O, 6),
        line(f"M{x:g} 520 L{x:g} 586", stripe, 3),
    ]


def foot(x: float, fill: str) -> List[str]:
    return [
        path(
            f"M{x - 12:g} 586 C{x - 12:g} 578 {x + 10:g} 578 {x + 14:g} 584 L{x + 30:g} 592 "
            f"C{x + 37:g} 596 {x + 35:g} 603 {x + 28:g} 603 L{x - 10:g} 603 C{x - 15:g} 603 {x - 15:g} 594 {x - 12:g} 586 Z",
            fill, O, 6,
        ),
        line(f"M{x + 6:g} 588 L{x + 24:g} 596", "#4a443a", 3),
    ]


def cuff(a: Tuple[float, float], b: Tuple[float, float], width: float) -> List[str]:
    """Three gold rings on a sleeve, near its end ``b``."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy)
    ux, uy, px, py = dx / n, dy / n, -dy / n, dx / n
    out = []
    for back in (16.0, 26.0, 36.0):
        cx, cy = b[0] - ux * back, b[1] - uy * back
        h = width / 2 - 2
        out.append(line(f"M{cx - px * h:.1f} {cy - py * h:.1f} L{cx + px * h:.1f} {cy + py * h:.1f}", GOLD, 5))
    return out


def parts() -> Dict[str, List[str]]:
    j = JOINTS
    shoulder, elbow, fist = (242.0, 346.0), (192.0, 420.0), (238.0, 472.0)
    far_shoulder, far_elbow, far_fist = (414.0, 346.0), (482.0, 416.0), (428.0, 472.0)
    out: Dict[str, List[str]] = {}

    # The far arm: akimbo, behind the coat. Its elbow shows at the side.
    out["far-arm-upper"] = tube(far_shoulder, far_elbow, 40, COAT_DARK)
    out["far-arm-lower"] = [*tube(far_elbow, far_fist, 36, COAT_DARK), *cuff(far_elbow, far_fist, 36)]

    out["far-leg"] = leg(j["far_leg"][1], "#27402a", GOLD_DARK)
    out["far-foot"] = foot(j["far_foot"][1], "#17140f")
    out["near-leg"] = leg(j["near_leg"][1], "#2f4a2e", GOLD)
    out["near-foot"] = foot(j["near_foot"][1], SHOE)

    # The coat: a box, wide at the shoulder, with a hem as straight as a rule.
    out["torso"] = [
        path("M226 352 C226 328 246 314 276 312 L380 312 C408 314 424 328 426 352 L434 516 C434 532 424 540 410 540 L244 540 C230 540 220 532 220 516 Z", COAT, O, 8),
        # The side away from the light, and the band of the hem.
        path("M226 352 C226 338 234 326 246 320 L250 506 L221 506 Z", COAT_DARK),
        path("M221 506 L433 506 L434 516 C434 532 424 540 410 540 L244 540 C230 540 220 532 220 516 Z", COAT_DARK),
        line("M262 326 C300 320 350 320 392 328", COAT_LIGHT, 6),
        # The collar, and the line the coat closes on.
        path("M312 312 L350 356 L354 312 Z", TRIM, O, 5),
        path("M354 312 L356 356 L396 312 Z", TRIM, O, 5),
        line("M353 356 L358 538", TRIM, 5),
        *[circle(366, y, 6, GOLD, GOLD_DARK, 3) for y in (440, 524)],
        # A red sash from the near shoulder to the far hip.
        path("M232 336 L262 314 L432 426 L433 458 L414 458 Z", RED, O, 5),
        line("M252 328 L424 446", "#d9534a", 4),
        # The belt and its buckle.
        path("M221 458 L433 458 L433 478 L221 478 Z", TRIM, O, 5),
        path("M340 454 L370 454 L370 482 L340 482 Z", GOLD, GOLD_DARK, 4),
        path("M348 462 L362 462 L362 474 L348 474 Z", TRIM),
        # He has more decorations than coat (Jon, 2026-10-13: "he needs more
        # badges and metals on his coat").
        # A rack of ribbons under the sash: four rows of four.
        *[
            path(f"M{242 + 19 * col} {372 + 13 * row} h17 v11 h-17 Z", colour, O, 2.5)
            for row, colours in enumerate((
                (RED, GOLD, BLUE, WHITE),
                (WHITE, RED, GOLD, BLUE),
                (BLUE, WHITE, RED, GOLD),
                (GOLD, BLUE, WHITE, RED),
            ))
            for col, colour in enumerate(colours)
        ],
        # Medals that hang over the sash: a disc, a star, a cross.
        *medal(374, 352, BLUE, "disc"),
        *medal(394, 358, RED, "star"),
        *medal(414, 366, "#7a4fa0", "cross"),
        # A second row of them under the ribbons.
        *medal(254, 430, RED, "star"),
        *medal(274, 430, "#7a4fa0", "disc"),
        *medal(294, 430, BLUE, "cross"),
        *medal(314, 430, GOLD_DARK, "disc"),
        # Two great orders under the belt, and pins along the sash.
        path(star(286, 508, 17, -90, points=8), GOLD, GOLD_DARK, 3),
        circle(286, 508, 6, RED, O, 2),
        path(star(408, 506, 15, -90, points=6), "#dfe3e6", "#7d858c", 3),
        circle(408, 506, 5, BLUE, O, 2),
        *[circle(x, y, 5, GOLD, GOLD_DARK, 2.5) for x, y in ((286, 346), (318, 367), (350, 388), (382, 409))],
        # The stars of his rank on the collar.
        path(star(332, 328, 8), GOLD, GOLD_DARK, 2),
        path(star(376, 327, 8), GOLD, GOLD_DARK, 2),
        # The epaulettes, with a fringe.
        path("M212 324 C212 312 226 306 250 306 L272 308 L272 326 L222 336 C215 336 212 330 212 324 Z", GOLD, O, 6),
        line("M222 332 L222 346 M234 330 L234 344 M246 328 L246 342 M258 326 L258 340", GOLD_DARK, 4),
        path("M440 324 C440 312 426 306 402 306 L384 308 L384 326 L430 336 C437 336 440 330 440 324 Z", GOLD, O, 6),
        line("M430 332 L430 346 M418 330 L418 344 M406 328 L406 342 M394 326 L394 340", GOLD_DARK, 4),
    ]

    # The swagger stick: under his far arm, and out ahead of him.
    out["baton"] = [
        line("M404 456 L528 414", O, 15),
        line("M404 456 L528 414", "#6b4424", 8),
        line("M516 418 L528 414", GOLD, 8),
    ]

    out["near-arm-upper"] = [*tube(shoulder, elbow, 44, COAT), line("M236 356 L204 404", COAT_LIGHT, 6)]
    out["near-arm-lower"] = [
        *tube(elbow, fist, 40, COAT),
        *cuff(elbow, fist, 40),
        circle(fist[0] + 6, fist[1] + 4, 18, SKIN, O, 6),
        line("M236 468 C242 464 250 466 254 472", SKIN_SHADE, 3),
    ]

    # The head: wide at the jaw, an ear, grey hair under the hat, the brows.
    out["head"] = [
        ellipse(286, 270, 14, 19, SKIN, O, 6),
        line("M284 262 C290 266 290 274 285 279", SKIN_SHADE, 3),
        path("M276 262 C272 226 300 204 338 204 C372 204 396 222 400 250 C404 262 404 276 400 290 C396 310 376 326 346 328 C310 330 282 304 276 262 Z", SKIN, O, 8),
        path("M277 262 C275 240 281 222 293 212 L302 252 C298 264 290 272 280 278 Z", "#7a736a"),
        path("M300 300 C312 316 330 324 348 324 C330 328 308 320 296 304 Z", SKIN_SHADE),
        # The brows: one thick line that goes down to the nose from each side.
        line("M338 222 L386 242", O, 11),
        line("M422 226 L400 234", O, 9),
    ]
    out["eye-open"] = [
        ellipse(362, 250, 15, 12, WHITE, O, 5),
        circle(369, 251, 5.5, O),
        # His far eye: the nose is over its lower part, and the rest shows
        # between the nose and the peak of the cap (Jon, 2026-10-13: "a
        # little bit of the eye peaking out so you can see it").
        ellipse(404, 244, 9, 10, WHITE, O, 4),
        circle(407, 243, 4, O),
    ]
    out["eye-shut"] = [
        line("M348 252 C356 244 368 244 376 252", O, 6),
        line("M396 245 C400 239 408 239 412 245", O, 5),
    ]
    # The nose is a part of its own, over the eyes and the mouth: it is in
    # front of his far eye, so it is drawn over the lower part of that eye.
    out["nose"] = [
        path("M388 258 C404 246 434 250 446 268 C456 284 448 304 426 306 C406 308 390 296 386 280 Z", NOSE, O, 7),
        line("M404 260 C414 256 426 258 434 266", "#f6c3ab", 5),
        line("M402 294 C408 298 416 298 420 294", SKIN_SHADE, 4),
    ]
    # The teeth, shut tight.
    out["mouth-grit"] = [
        path("M332 292 C332 284 340 280 350 280 L394 284 C402 285 406 292 404 300 L400 312 C398 319 392 321 386 321 L350 321 C338 321 332 312 332 302 Z", WHITE, O, 7),
        line("M334 301 L403 303", O, 4),
        line("M350 282 L350 320 M364 282 L364 320 M378 283 L378 320 M391 285 L391 320", O, 3.5),
    ]
    # The mouth open: he shouts.
    out["mouth-open"] = [
        path("M332 288 C332 280 340 276 350 276 L396 280 C404 281 408 288 406 298 L400 326 C398 334 390 338 382 338 L352 338 C338 338 332 324 332 306 Z", "#5a1f24", O, 7),
        path("M336 286 C336 282 342 280 350 280 L394 283 C400 284 403 288 402 294 L338 292 Z", WHITE),
        line("M352 281 L352 292 M366 282 L366 293 M380 283 L380 293 M392 284 L392 294", O, 3),
        ellipse(368, 324, 17, 9, "#e2777c"),
    ]

    # The hat: an officer's peaked cap (Jon, 2026-10-13: "Just a normal
    # officer hat"). A wide crown that is higher at the front, a dark band
    # with a gold strap and its button, a black peak, a gold badge.
    out["hat"] = [
        path("M256 192 C248 168 260 150 286 146 C322 130 382 120 414 130 C434 138 436 162 426 180 C422 190 414 196 404 198 C376 186 300 186 272 196 C264 198 258 196 256 192 Z", HAT, O, 8),
        path("M256 192 C250 174 256 160 270 152 C268 166 272 182 282 192 C276 194 274 195 272 196 C264 198 258 196 256 192 Z", HAT_DARK),
        line("M276 158 C312 142 376 132 414 140", HAT_LIGHT, 5),
        path("M272 196 C300 186 376 186 404 198 L405 218 C376 206 300 206 274 218 Z", TRIM, O, 7),
        line("M277 212 C303 201 373 201 402 212", GOLD, 6),
        circle(283, 210, 6, GOLD, GOLD_DARK, 3),
        line("M344 199 L346 208", GOLD_DARK, 5),
        path("M354 208 C386 200 430 208 450 228 C428 237 390 237 358 229 Z", "#15171a", O, 7),
        line("M372 214 C396 211 420 214 436 222", "#59606a", 4),
        # The badge: a gold star in a gold ring.
        circle(390, 164, 15, HAT_DARK, GOLD, 4),
        path(star(390, 164, 11), GOLD, GOLD_DARK, 2),
    ]
    return out


#: The parts, in the order they are drawn: (group id, label, part, bone, z, opacity channel).
LAYERS = [
    ("far-arm-upper", "Far Arm - Upper", "far_arm_upper", "far_arm_upper", 4, ""),
    ("far-arm-lower", "Far Arm - Lower", "far_arm_lower", "far_arm_lower", 5, ""),
    ("baton", "Swagger Stick", "baton", "far_arm_lower", 6, ""),
    ("far-leg", "Far Leg", "far_leg", "far_leg", 8, ""),
    ("far-foot", "Far Foot", "far_foot", "far_foot", 9, ""),
    ("near-leg", "Near Leg", "near_leg", "near_leg", 10, ""),
    ("near-foot", "Near Foot", "near_foot", "near_foot", 11, ""),
    ("torso", "Coat", "torso", "torso", 20, ""),
    ("near-arm-upper", "Near Arm - Upper", "near_arm_upper", "near_arm_upper", 30, ""),
    ("near-arm-lower", "Near Arm - Lower", "near_arm_lower", "near_arm_lower", 31, ""),
    ("head", "Head", "head", "head", 40, ""),
    ("eye-open", "Eyes - Open", "eye_open", "head", 41, "eye_open"),
    ("eye-shut", "Eyes - Shut", "eye_shut", "head", 41, "eye_shut"),
    ("mouth-grit", "Mouth - Teeth Shut", "mouth_grit", "head", 42, "mouth_grit"),
    ("mouth-open", "Mouth - Open", "mouth_open", "head", 42, "mouth_open"),
    ("nose", "Nose", "nose", "head", 43, ""),
    ("hat", "Hat", "hat", "hat", 50, ""),
]


def svg() -> str:
    drawn = parts()
    groups = []
    for group, label, part, bone, z, _channel in LAYERS:
        inner = "\n".join(f"      {element}" for element in drawn[group])
        groups.append(
            f'    <g id="{group}" inkscape:groupmode="layer" inkscape:label="{label}" '
            f'data-rig-part="{part}" data-rig-bone="{bone}" data-rig-z="{z}">\n{inner}\n    </g>'
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg"\n'
        '     xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"\n'
        '     width="640mm" height="640mm" viewBox="0 0 640 640"\n'
        '     data-character-design="absurd-general-v2">\n'
        f'  <g id="absurd-general" inkscape:groupmode="layer" inkscape:label="{VIEW}">\n'
        + "\n".join(groups)
        + "\n  </g>\n</svg>\n"
    )


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".svg.tmp")
    tmp.write_text(svg(), encoding="utf8")
    tmp.replace(OUT)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
