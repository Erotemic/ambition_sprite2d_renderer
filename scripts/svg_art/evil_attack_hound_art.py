#!/usr/bin/env python3
"""Draw the attack hound of Castle Godwin (the Evil dimension).

    uv run python scripts/svg_art/evil_attack_hound_art.py
    uv run python scripts/build_evil_attack_hound_rig.py

Writes ``data/characters/evil_attack_hound/evil_attack_hound_side.svg``.

A lean guard dog of the regime, like a German shepherd: a dark coat (a
black saddle on dark rust), tall ears that point forward, raised hackles,
an amber eye under a low brow, and a snarl that shows the teeth. A black
collar with steel spikes and a red stripe; its red tag carries the mark of
the regime (``_evil_faction.cog``: the black cog with a hole, on a white
disc, on red).

THE JOINTS ARE THE COMPANION DOG'S, as for the house dogs
(``house_dogs_art.py``): the same parts about the same joints, and legs
``LEG_SCALE`` as long. The hound has one more joint: the hinge of its lower
jaw (``JAW_HINGE``), so it can bite. Its clips are its own
(``scripts/build_evil_attack_hound_rig.py``).

Drawn side on, facing right, in SVG units of 640 x 512. NO drop shadow.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for entry in (ROOT, HERE):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from house_dogs_art import PAW_JOINT_Y, fit_leg, fit_legs, layer, legs, line, path, shift  # noqa: E402

from ambition_sprite2d_renderer.targets.characters import _evil_faction  # noqa: E402

NAME = "evil_attack_hound"
SVG_NAME = f"{NAME}_side"
VIEW = "Attack Hound - Side Right"
OUT = ROOT / "ambition_sprite2d_renderer" / "data" / "characters" / NAME / f"{SVG_NAME}.svg"

#: The legs, as a part of the companion dog's: long and lean.
LEG_SCALE = 1.1
LEG_THICKNESS = 0.72
#: The paws, as a part of the companion dog's, about the joint of each.
PAW_SCALE = 0.8
#: Where the joint of each paw is across (SVG units), as the companion dog has it.
PAW_JOINT_X = {"far-hind-paw": 252.0, "far-fore-paw": 375.0, "near-hind-paw": 258.0, "near-fore-paw": 417.0}
#: The hinge of the lower jaw (SVG units). The jaw turns about it.
JAW_HINGE = (532.0, 254.0)
#: The joint of the head (SVG units), as the companion dog has it.
HEAD_PIVOT = (473.0, 219.0)

P: Dict[str, str] = {
    "outline": "#120d0f",
    # The black saddle.
    "coat": "#362e32", "coat_light": "#5e5157", "coat_dark": "#251f22",
    # The dark rust of the points.
    "tan": "#7c4325", "tan_light": "#9c5a31", "tan_dark": "#5b2f1b",
    # What ``legs`` reads.
    "far_upper": "#262023", "far_lower": "#4f2a18", "far_light": "#643721", "far_paw": "#5c321e",
    "leg": "#7c4325", "leg_light": "#9a5830", "paw": "#8a4b29", "toe": "#341c11",
    "cream": "#e8dcc4", "eye_rim": "#0c0809",
}
TOOTH = "#f1e9d2"
TOOTH_LINE = "#5c4b3c"
GUM = "#8e2b3b"
MOUTH = "#3b0f17"
TONGUE = "#b24e5c"


def _hex(colour: Sequence[int]) -> str:
    return "#%02x%02x%02x" % tuple(colour[:3])


class _SvgPen:
    """Takes the drawing calls of ``_evil_faction.cog`` and keeps them as SVG
    elements, so the mark on the tag is the mark of the shared module."""

    def __init__(self) -> None:
        self.out: List[str] = []

    def poly(self, _d, pts: Sequence[Tuple[float, float]], colour) -> None:
        points = " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
        self.out.append(f'<polygon points="{points}" fill="{_hex(colour)}"/>')

    def oval(self, _d, c: Tuple[float, float], rx: float, ry: float, colour) -> None:
        self.out.append(f'<ellipse cx="{c[0]:.2f}" cy="{c[1]:.2f}" rx="{rx:.2f}" ry="{ry:.2f}" fill="{_hex(colour)}"/>')


def regime_tag(c: Tuple[float, float], r: float) -> List[str]:
    """The red tag with the mark: a white disc and the black cog on it."""
    pen = _SvgPen()
    pen.out.append(f'<circle cx="{c[0]:g}" cy="{c[1]:g}" r="{r:g}" fill="{_hex(_evil_faction.RED)}" stroke="{P["outline"]}" stroke-width="4"/>')
    pen.out.append(f'<circle cx="{c[0]:g}" cy="{c[1]:g}" r="{r * 0.72:g}" fill="{_hex(_evil_faction.DISC)}"/>')
    _evil_faction.cog(pen, None, c, r * 0.6)
    return pen.out


def tooth(tip: Tuple[float, float], root: Tuple[float, float], half: float) -> str:
    """A tooth: a narrow triangle from its root (on the gum) to its tip."""
    (tx, ty), (rx, ry) = tip, root
    return path(f"M{rx - half:g} {ry:g} L{rx + half:g} {ry:g} L{tx:g} {ty:g} Z", TOOTH, TOOTH_LINE, 2.2)


def hound() -> Dict[str, List[str]]:
    p, o = P, P["outline"]
    parts = legs(p)
    # Lean, hard legs: a line of muscle on each near leg.
    parts["near-hind-upper"] += [
        path("M246 300 C266 296 286 306 296 326 C280 322 262 320 240 326 C240 314 242 306 246 300 Z", p["coat_dark"]),
        line("M262 336 C274 346 284 352 292 352", p["tan_dark"], 4),
    ]
    parts["near-fore-upper"] += [line("M430 300 C436 320 432 344 424 364", p["coat_dark"], 4)]
    for group in ("near-hind-paw", "near-fore-paw", "far-hind-paw", "far-fore-paw"):
        # Dark claws at the front of each paw.
        x0 = {"near-hind-paw": 316, "near-fore-paw": 468, "far-hind-paw": 298, "far-fore-paw": 418}[group]
        parts[group].append(line(f"M{x0 - 4} 476 L{x0 + 4} 482 M{x0 - 4} 468 L{x0 + 4} 472", "#100b0c", 3))
        jx, jy = PAW_JOINT_X[group], PAW_JOINT_Y[group]
        parts[group] = fit_leg(parts[group], lambda x, y, jx=jx, jy=jy: (jx + (x - jx) * PAW_SCALE, jy + (y - jy) * PAW_SCALE))

    # A thick brush of a tail: black over it, rust under it.
    parts["tail-base"] = [
        path("M214 284 C196 288 182 280 170 278 C156 276 146 262 138 252 C128 238 124 222 128 208 C134 196 150 198 156 210 C166 230 186 240 216 240 Z", p["coat"], o, 8),
        line("M204 276 C184 276 164 266 148 250 C140 240 134 230 132 220", p["tan_dark"], 8),
        line("M196 246 C178 240 162 226 154 212", p["coat_light"], 5),
    ]
    parts["tail-tip"] = [
        path("M134 224 C120 206 108 182 102 144 C118 158 142 176 156 200 C161 211 159 223 152 228 C146 232 138 230 134 224 Z", p["coat"], o, 8),
        line("M110 160 C116 182 126 202 138 216", p["tan_dark"], 6),
        line("M120 162 C134 174 146 188 152 204", p["coat_light"], 4),
    ]

    # Deep in the chest, tucked up at the waist. Rust under, a black saddle over.
    parts["body"] = [
        path("M198 254 C212 228 246 214 290 214 C326 213 350 212 384 206 C424 198 458 212 476 244 C490 274 486 322 464 342 C442 358 408 348 384 328 C348 300 302 300 262 304 C222 308 188 296 198 254 Z", p["tan"], o, 9),
        path("M200 256 C214 230 248 216 290 216 C326 215 350 214 384 208 C412 203 436 208 452 222 C454 254 438 278 406 286 C368 292 332 280 298 284 C264 288 230 296 208 292 C196 282 196 268 200 256 Z", p["coat"]),
        line("M206 266 C214 240 240 224 276 220 M300 218 C330 218 356 216 386 212", p["coat_light"], 6),
        # The ribs and the tuck of the belly.
        line("M410 300 C420 312 424 324 422 334", p["tan_dark"], 4),
        line("M392 296 C400 308 402 318 400 326", p["tan_dark"], 4),
        line("M272 302 C304 300 334 298 364 310", p["tan_light"], 4),
    ]

    # A thick neck with the hackles up, a rust throat and a spiked collar.
    hackles = (
        "M370 214 L376 200 L384 210 L392 196 L400 208 L408 192 L416 206 L425 188 L433 204 L442 184 L450 200 "
        "L460 180 L467 198 L478 180 L484 198 L496 184 L500 206 L504 228 C470 216 420 214 370 214 Z"
    )
    collar = "M446 268 C462 278 482 278 499 266 L497 288 C482 300 462 300 448 292 Z"
    spikes = []
    for (x, y, dx, dy) in ((454, 294, -3, 11), (466, 298, -1, 12), (478, 298, 1, 12), (490, 294, 3, 11), (500, 280, 12, 2)):
        nx, ny = -dy * 0.36, dx * 0.36
        spikes.append(path(f"M{x - nx:g} {y - ny:g} L{x + dx:g} {y + dy:g} L{x + nx:g} {y + ny:g} Z", "#c9ced6", "#3e4249", 2.5))
    parts["neck"] = [
        path(hackles, p["coat"], o, 7),
        path("M429 226 C454 204 483 207 503 227 L497 289 C479 314 457 331 439 329 C453 296 449 255 429 226 Z", p["coat"], o, 8),
        path("M459 232 C473 231 488 238 497 253 L491 290 C480 311 461 326 448 322 C466 294 469 256 459 232 Z", p["tan"]),
        line("M466 244 C474 262 474 284 466 304", p["tan_light"], 4),
        path(collar, "#151416", o, 5),
        line("M447 280 C463 290 482 290 498 277", _hex(_evil_faction.RED), 6),
        *spikes,
        line("M472 298 L472 306", "#9aa0a8", 3),
        *regime_tag((472.0, 320.0), 16.0),
    ]

    # The pointed ear, tall and turned forward. The far ear is darker and behind.
    ear_edge = "M456 198 C458 160 474 122 500 90 C504 86 510 88 511 95 C517 128 519 156 515 182 C499 194 474 200 456 198 Z"
    ear_inner = "M470 186 C474 158 486 132 500 112 C505 138 507 160 505 178 C495 184 482 187 470 186 Z"
    ear_fur = "M476 182 C480 166 486 152 494 140"

    # The head: a black skull and muzzle, rust cheeks and brows.
    skull = "M452 196 C466 166 502 154 534 160 C560 166 578 188 578 214 C578 242 562 262 538 270 C506 280 474 268 460 250 C450 236 446 212 452 196 Z"
    muzzle = "M536 204 C560 196 592 200 614 208 C626 213 632 224 628 232 C622 238 614 238 606 238 C598 238 590 244 580 250 L548 254 C534 250 528 236 530 222 C531 212 532 207 536 204 Z"
    gum = "M552 252 C570 252 586 246 598 237 L620 235 L621 246 C600 252 576 258 554 259 Z"
    parts["head"] = [
        path(shift(ear_edge, 34, 6), "#151112", o, 8),
        path(shift(ear_inner, 34, 6), "#3d2723"),
        path(skull, p["coat"], o, 9),
        line("M470 190 C486 172 512 164 540 168", p["coat_light"], 6),
        path("M478 238 C494 226 524 228 542 244 C538 262 518 272 496 268 C484 262 474 250 478 238 Z", p["tan"]),
        path("M486 196 C491 188 503 187 510 191 C511 196 506 199 499 199 C492 200 488 199 486 196 Z", p["tan_light"]),
        # The gum shows under the lip that the snarl pulls up.
        path(gum, GUM, o, 3),
        path(muzzle, p["coat_dark"], o, 8),
        # The snarl: folds of skin on the top of the muzzle.
        line("M574 205 L568 219 M586 205 L580 221 M598 208 L592 222", p["coat_light"], 3.5),
        line("M552 252 C568 252 584 248 598 238 L620 236", "#4a1a24", 3),
        # The upper teeth: a long fang and a row of short, sharp teeth.
        tooth((603.0, 276.0), (601.0, 250.0), 6.5),
        tooth((612.0, 259.0), (612.0, 248.0), 3.2),
        tooth((619.0, 256.0), (619.0, 246.0), 3.0),
        tooth((565.0, 266.0), (565.0, 257.0), 4.5),
        tooth((577.0, 265.0), (577.0, 255.0), 4.5),
        tooth((589.0, 263.0), (589.0, 252.0), 4.5),
        path("M604 204 C614 199 626 203 630 212 C632 220 626 227 618 227 C610 227 604 221 602 213 Z", "#0b0809", "#050404", 3),
        line("M612 207 C617 205 622 207 624 211", "#5b5458", 3),
    ]
    # The lower jaw, about ``JAW_HINGE``. Its teeth point up, in front of the lip.
    parts["mouth-inside"] = [
        path("M532 256 C556 246 590 236 618 230 L624 262 C598 268 562 268 534 262 Z", MOUTH),
        path("M546 254 C566 249 590 247 606 249 C611 253 607 258 598 259 C578 261 560 260 546 256 Z", TONGUE),
    ]
    parts["jaw"] = [
        path("M528 250 C552 262 584 264 612 258 C620 257 624 263 620 270 C604 282 570 286 546 282 C530 278 522 264 528 250 Z", p["coat_dark"], o, 7),
        path("M544 274 C566 280 594 278 612 268 C606 278 584 284 560 282 C552 280 546 278 544 274 Z", p["tan_dark"]),
    ]
    parts["lower-teeth"] = [
        tooth((590.0, 244.0), (590.0, 263.0), 5.0),
        tooth((604.0, 252.0), (604.0, 261.0), 3.0),
        tooth((612.0, 251.0), (612.0, 259.0), 3.0),
        tooth((568.0, 256.0), (568.0, 264.0), 3.6),
        tooth((579.0, 255.0), (579.0, 264.0), 3.6),
    ]
    # The amber eye, almond and narrow, and the low brow that cuts across it.
    parts["eye-open"] = [
        path("M493 226 C501 211 523 207 539 218 C531 231 509 235 493 226 Z", P["eye_rim"]),
        '<circle cx="518" cy="222" r="8" fill="#e8a51c"/>',
        '<circle cx="519.5" cy="222.5" r="3.8" fill="#0b0708"/>',
        '<circle cx="522" cy="219.5" r="1.7" fill="#fff6d8"/>',
        path("M484 200 C504 197 530 206 546 223 L539 229 C524 216 506 212 486 215 Z", p["coat"], o, 3),
        line("M492 205 C508 204 526 210 540 222", p["coat_light"], 2.5),
    ]
    parts["eye-x"] = [
        '<ellipse cx="516" cy="221" rx="13" ry="12" fill="#2a2427"/>',
        line("M507 212 L525 230 M525 212 L507 230", "#d9d2c6", 5),
    ]
    parts["ear"] = [
        path(ear_edge, p["coat"], o, 8),
        path(ear_inner, "#5a3a33"),
        line(ear_fur, p["tan"], 4),
    ]
    return parts


#: The parts, in the order they are drawn: (group id, label, part, bone, z).
LAYERS = [
    ("tail-base", "Tail - Base", "tail_base", "tail_base", 1),
    ("tail-tip", "Tail - Tip", "tail_tip", "tail_tip", 2),
    ("far-hind-upper", "Far Hind Leg - Upper", "far_hind_upper", "far_hind_upper", 5),
    ("far-hind-lower", "Far Hind Leg - Lower", "far_hind_lower", "far_hind_lower", 6),
    ("far-hind-paw", "Far Hind Paw", "far_hind_paw", "far_hind_paw", 7),
    ("far-fore-upper", "Far Foreleg - Upper", "far_fore_upper", "far_fore_upper", 8),
    ("far-fore-lower", "Far Foreleg - Lower", "far_fore_lower", "far_fore_lower", 9),
    ("far-fore-paw", "Far Forepaw", "far_fore_paw", "far_fore_paw", 10),
    ("body", "Body", "body", "body", 20),
    ("near-hind-upper", "Near Hind Leg - Upper", "near_hind_upper", "near_hind_upper", 30),
    ("near-hind-lower", "Near Hind Leg - Lower", "near_hind_lower", "near_hind_lower", 31),
    ("near-hind-paw", "Near Hind Paw", "near_hind_paw", "near_hind_paw", 32),
    ("near-fore-upper", "Near Foreleg - Upper", "near_fore_upper", "near_fore_upper", 33),
    ("near-fore-lower", "Near Foreleg - Lower", "near_fore_lower", "near_fore_lower", 34),
    ("near-fore-paw", "Near Forepaw", "near_fore_paw", "near_fore_paw", 35),
    ("mouth-inside", "Mouth - Inside", "mouth_inside", "jaw", 37),
    ("neck", "Neck, Hackles and Collar", "neck", "body", 38),
    ("jaw", "Lower Jaw", "jaw", "jaw", 39),
    ("head", "Head, Muzzle and Upper Teeth", "head", "head", 40),
    ("eye-open", "Eye - Open", "eye_open", "head", 41),
    ("eye-x", "Eye - Death X", "eye_x", "head", 41),
    ("ear", "Ear", "ear", "ear", 42),
    ("lower-teeth", "Lower Teeth", "lower_teeth", "jaw", 43),
]


def svg() -> str:
    parts = hound()
    fit_legs(parts, LEG_SCALE, LEG_THICKNESS)
    missing = [group for group, *_ in LAYERS if group not in parts]
    if missing:
        raise RuntimeError(f"{NAME} has no drawing for: {', '.join(missing)}")
    groups = "\n".join(layer(group, label, part, bone, z, parts[group]) for group, label, part, bone, z in LAYERS)
    slug = SVG_NAME.replace("_", "-")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg"\n'
        '     xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"\n'
        '     width="640mm" height="512mm" viewBox="0 0 640 512"\n'
        f'     data-character-design="{slug}-v1">\n'
        f'  <g id="{slug}" inkscape:groupmode="layer" inkscape:label="{VIEW}">\n'
        f"{groups}\n"
        "  </g>\n"
        "</svg>\n"
    )


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".svg.tmp")
    tmp.write_text(svg(), encoding="utf8")
    tmp.replace(OUT)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
