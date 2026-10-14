#!/usr/bin/env python3
"""Draw the three house dogs, each from a photograph of a dog of Jon's.

    uv run python scripts/svg_art/house_dogs_art.py
    uv run python scripts/build_house_dog_rigs.py

Writes ``data/characters/<name>/<name>_side.svg`` for:

* ``dog_honey`` (Honey, 35 lb, the smallest): a short orange dog like a fox.
  Two very large ears with dark edges (the tip of her right ear has a small
  flap, so she has a drawing of each side), a pale pip of an eyebrow, grey
  about the nose, a small white patch on the chest, a thick brush of a tail that is pale under
  it, short legs. No collar.
* ``dog_roadie`` (Roadie, 50 lb, the biggest): a cattle dog. A tan head and
  legs, a blue-grey saddle with flecks, a ruff at the neck, a brush of a tail
  with a white end, an orange collar.
* ``dog_bezoar`` (Bezoar, "Bea", 40 lb, taller than Honey and lanky): a slim
  fawn dog on long thin legs. A muzzle that goes dark toward the nose, a
  dark pip of an eyebrow, two ears with a slight flop and dark tips (each
  stands up, and its end hangs forward), a thin tail with a dark end, a brown collar with a
  pattern and a blue tag in the shape of a bone.

THE JOINTS ARE THE COMPANION DOG'S. Each drawing has the companion dog's
parts, with its part names, about the same joints
(``data/characters/companion_dog/companion_dog_side.svg``), so the companion
dog's rig and its clips play on each (``scripts/build_house_dog_rigs.py``).
What is the dog's own is its shape and its coat: the head, the ears, the
tail, the marks on the body, the collar, and how long its legs are
(``_house_dog.LEG_SCALE``: the builder moves the leg joints by the same rule).

Each is drawn side on, facing right, in the SVG units of the companion dog
(640 x 512). The SVGs own the art after this script has run once.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Callable, Dict, List

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import json  # noqa: E402

from ambition_sprite2d_renderer.targets.characters._house_dog import (  # noqa: E402
    COMPANION_RIG_PATH,
    LEFT_SIDE,
    LEG_SCALE,
    LEG_THICKNESS,
    leg_y,
)

DATA = ROOT / "ambition_sprite2d_renderer" / "data" / "characters"

Palette = Dict[str, str]


def shift(d: str, dx: float, dy: float) -> str:
    """Path data moved by (dx, dy). The paths here have absolute commands
    with whole pairs of numbers only (M, L, C, Z)."""
    numbers = iter(re.findall(r"-?\d+(?:\.\d+)?", d))
    pairs = [(float(x) + dx, float(y) + dy) for x, y in zip(numbers, numbers)]
    moved = iter(pairs)

    def put(_match: re.Match) -> str:
        x, y = next(moved)
        return f"{x:g} {y:g}"

    return re.sub(r"-?\d+(?:\.\d+)?\s+-?\d+(?:\.\d+)?", put, d)


def _on_points(d: str, move: Callable[[float, float], tuple]) -> str:
    numbers = iter(re.findall(r"-?\d+(?:\.\d+)?", d))
    moved = iter([move(float(x), float(y)) for x, y in zip(numbers, numbers)])

    def put(_match: re.Match) -> str:
        x, y = next(moved)
        return f"{x:g} {round(y, 2):g}"

    return re.sub(r"-?\d+(?:\.\d+)?\s+-?\d+(?:\.\d+)?", put, d)


def fit_leg(elements: List[str], move: Callable[[float, float], tuple]) -> List[str]:
    """The elements of one leg part, with each point moved by ``move``."""
    out = []
    for element in elements:
        element = re.sub(r'd="([^"]+)"', lambda m: f'd="{_on_points(m.group(1), move)}"', element)
        element = re.sub(r'cx="([^"]+)" cy="([^"]+)"', lambda m: 'cx="%g" cy="%g"' % move(float(m.group(1)), float(m.group(2))), element)
        out.append(element)
    return out


#: The height of the joint of each paw, in the companion dog's drawing.
PAW_JOINT_Y = {"far-hind-paw": 455.0, "far-fore-paw": 457.0, "near-hind-paw": 455.0, "near-fore-paw": 457.0}


def fit_legs(parts: Dict[str, List[str]], scale: float, thickness: float = 1.0) -> None:
    """Make the legs ``scale`` as long and ``thickness`` as thick: a leg part
    is stretched under the line of the hips and made thin about its own
    joint, and a paw goes with its joint and keeps its shape."""
    joints = json.loads(COMPANION_RIG_PATH.read_text())["parts"]
    joint_x = {part["name"].replace("_", "-"): float(part["pivot"][0]) for part in joints}
    for group in list(parts):
        if group in PAW_JOINT_Y:
            lift = leg_y(PAW_JOINT_Y[group], scale) - PAW_JOINT_Y[group]
            parts[group] = fit_leg(parts[group], lambda x, y: (x, y + lift))
        elif group.endswith(("-upper", "-lower")):
            about = joint_x[group]
            parts[group] = fit_leg(parts[group], lambda x, y: (about + (x - about) * thickness, leg_y(y, scale)))


def layer(group_id: str, label: str, part: str, bone: str, z: int, body: List[str]) -> str:
    inner = "\n".join(f"      {line}" for line in body)
    return (
        f'    <g id="{group_id}" inkscape:groupmode="layer" inkscape:label="{label}" '
        f'data-rig-part="{part}" data-rig-bone="{bone}" data-rig-z="{z}">\n{inner}\n    </g>'
    )


def path(d: str, fill: str, stroke: str = "", width: float = 0.0, extra: str = "") -> str:
    out = f'<path d="{d}" fill="{fill}"'
    if stroke:
        out += f' stroke="{stroke}" stroke-width="{width:g}" stroke-linejoin="round"'
    return out + (f" {extra}" if extra else "") + "/>"


def line(d: str, stroke: str, width: float) -> str:
    return f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="{width:g}" stroke-linecap="round"/>'


def legs(p: Palette) -> Dict[str, List[str]]:
    """The eight leg parts and four paws. One shape for the three dogs: the
    joints of the companion dog are in these."""
    o = p["outline"]
    return {
        "far-hind-upper": [path("M264 294 C276 306 282 327 280 348 C279 364 267 377 252 376 C238 373 232 360 235 345 L237 312 Z", p["far_upper"], o, 8)],
        "far-hind-lower": [path("M257 354 C267 351 278 359 280 371 L269 448 C267 460 255 467 246 461 C238 457 236 447 240 435 L240 371 C240 362 247 355 257 354 Z", p["far_lower"], o, 8)],
        "far-hind-paw": [
            path("M244 444 C257 437 268 443 275 453 L291 458 C301 461 305 472 299 480 C291 486 267 484 247 482 C231 480 228 467 235 454 Z", p["far_paw"], o, 8),
            line("M271 460 L273 479 M286 464 L289 479", p["toe"], 4),
        ],
        "far-fore-upper": [path("M389 282 C401 284 408 295 407 311 L396 374 C393 391 377 399 365 391 C353 385 352 373 356 361 L363 296 Z", p["far_upper"], o, 8)],
        "far-fore-lower": [
            path("M375 371 C388 368 398 378 397 391 L395 459 C394 471 385 477 374 475 C363 473 360 464 363 452 L358 393 C357 381 364 373 375 371 Z", p["far_lower"], o, 8),
            line("M368 403 L370 455", p["far_light"], 7),
        ],
        "far-fore-paw": [
            path("M368 447 C380 441 391 448 399 457 L411 459 C421 461 427 472 420 481 C413 487 382 485 364 482 C351 480 349 468 356 456 Z", p["far_paw"], o, 8),
            line("M390 460 L391 480 M404 463 L406 480", p["toe"], 4),
        ],
        "near-hind-upper": [
            path("M252 291 C279 286 299 307 303 337 C306 362 289 382 270 384 C247 386 232 370 233 349 C234 327 239 304 252 291 Z", p["coat"], o, 8),
            line("M255 307 C272 302 290 317 290 340", p["coat_light"], 7),
        ],
        "near-hind-lower": [
            path("M271 364 C286 358 299 368 299 384 C296 407 279 421 276 453 C275 466 266 474 254 470 C242 466 240 455 245 443 L257 386 C257 376 262 368 271 364 Z", p["leg"], o, 8),
            line("M280 392 L261 444", p["leg_light"], 7),
        ],
        "near-hind-paw": [
            path("M250 446 C267 438 282 447 291 457 L309 459 C322 462 327 474 319 482 C312 488 276 486 254 483 C236 481 231 469 238 456 Z", p["paw"], o, 8),
            line("M281 460 L283 481 M300 463 L302 481", p["toe"], 4),
        ],
        "near-fore-upper": [
            path("M422 283 C441 282 452 297 448 318 L434 384 C431 400 413 408 399 398 C388 389 390 375 395 360 L402 302 C405 290 411 284 422 283 Z", p["coat"], o, 8),
            line("M420 302 L410 363", p["coat_light"], 8),
        ],
        "near-fore-lower": [
            path("M413 378 C429 373 439 382 439 397 L436 456 C436 470 428 478 414 476 C402 475 397 466 401 453 L398 398 C397 389 403 381 413 378 Z", p["leg"], o, 8),
            line("M411 404 L414 449", p["leg_light"], 7),
        ],
        "near-fore-paw": [
            path("M407 447 C423 440 437 447 446 458 L462 461 C475 465 478 476 469 483 C461 488 425 486 405 483 C391 481 387 468 395 456 Z", p["paw"], o, 8),
            line("M436 461 L438 482 M454 464 L456 482", p["toe"], 4),
        ],
    }


def eyes(p: Palette, at: tuple = (514.0, 224.0), size: float = 1.0) -> Dict[str, List[str]]:
    """A dark eye with a brown iris, and the two other faces of the eye."""
    x, y = at
    k = size
    return {
        "eye-open": [
            f'<ellipse cx="{x:g}" cy="{y:g}" rx="{9 * k:g}" ry="{10.5 * k:g}" fill="{p["eye_rim"]}"/>',
            f'<ellipse cx="{x + 1:g}" cy="{y + 0.5:g}" rx="{6.6 * k:g}" ry="{8 * k:g}" fill="{p["iris"]}"/>',
            f'<ellipse cx="{x + 1.5:g}" cy="{y + 1:g}" rx="{4 * k:g}" ry="{5.2 * k:g}" fill="#17110f"/>',
            f'<circle cx="{x + 4 * k:g}" cy="{y - 3.5 * k:g}" r="{2.4 * k:g}" fill="#ffffff"/>',
        ],
        "eye-x": [
            f'<ellipse cx="{x + 10:g}" cy="{y:g}" rx="13" ry="15" fill="{p["cream"]}"/>',
            line(f"M{x + 1:g} {y - 10:g} L{x + 19:g} {y + 10:g} M{x + 19:g} {y - 10:g} L{x + 1:g} {y + 10:g}", "#242126", 6),
        ],
        "eye-happy": [line(f"M{x - 9:g} {y + 4:g} C{x - 5:g} {y - 7:g} {x + 7:g} {y - 8:g} {x + 12:g} {y + 3:g}", p["eye_rim"], 5)],
    }


def bark_mouth(jaw: str, outline: str, dx: float = 0.0, dy: float = 0.0) -> List[str]:
    """The mouth in the frames of a bark: the mouth at rest (``mouth``),
    open a little more, with the tongue in it. No wider than the mouth at
    rest (Jon, 2026-10-13, of a wide one: "too wide too big"). It is shown
    in place of the mouth at rest, behind the head as that is.
    """
    return [
        path(shift("M548 262 C564 270 586 272 606 264 C607 280 599 292 586 296 C566 298 552 286 546 268 Z", dx, dy), "#5a2630"),
        path(shift("M560 284 C570 280 586 281 596 285 C594 292 586 296 576 296 C568 295 563 290 560 284 Z", dx, dy), "#ec8a93"),
        path(shift("M530 270 C542 290 566 300 590 296 C598 294 603 288 604 282 C606 294 598 310 580 316 C560 320 540 312 528 296 C524 286 525 276 530 270 Z", dx, dy), jaw, outline, 7),
    ]

NOSE = "M588 216 C599 211 611 216 617 225 C621 233 615 244 603 244 C594 244 588 236 586 228 Z"
SKULL = "M453 193 C468 166 505 154 538 162 C564 168 581 190 579 220 C577 246 562 266 536 274 C504 283 473 269 458 247 C448 231 445 207 453 193 Z"
MUZZLE = "M542 218 C561 208 583 211 603 220 C616 228 622 244 617 257 C610 269 582 270 557 267 L533 251 C529 237 533 224 542 218 Z"
BODY = "M196 245 C216 216 250 201 291 206 C326 208 349 218 382 215 C420 208 457 220 474 250 C486 273 475 312 453 328 C425 346 392 335 366 333 C326 330 285 349 244 341 C208 333 183 300 196 245 Z"
NECK = "M429 226 C454 204 483 207 503 227 L497 289 C479 314 457 331 439 329 C453 296 449 255 429 226 Z"
# A collar, where the neck shows under the head.
COLLAR = "M446 268 C462 278 482 278 499 266 L497 286 C482 298 462 298 448 290 Z"
NECK_FRONT = "M459 230 C473 229 488 237 497 253 L491 290 C480 311 461 326 448 322 C466 294 469 256 459 230 Z"

#: A mark over the eye, about (515, 203): the pip of an eyebrow.
BROW_PIP = "M506 204 C507 198 514 196 521 197 C526 198 528 203 525 206 C519 209 509 209 506 204 Z"
# An ear that stands up, about the ear joint (478, 180).
EAR_UP = "M456 198 C449 160 450 124 465 92 C469 83 478 83 483 91 C498 118 509 146 513 176 C499 191 474 199 456 198 Z"
EAR_UP_INNER = "M468 184 C463 156 464 130 472 108 C485 130 495 152 499 172 C489 180 478 184 468 184 Z"


def mouth(jaw: str, outline: str, dx: float = 0.0, dy: float = 0.0) -> List[str]:
    """An open mouth: the dark of the mouth, the lower jaw, and the tongue.

    The tongue lies ON the lower jaw and hangs over its front lip. This is
    a part of its own (``rest-mouth``), BEHIND the head, so the muzzle is
    drawn over the root of the tongue: a tongue drawn over the muzzle hangs
    from the top of the mouth. A bark shows ``bark-mouth`` in its place.
    """
    return [
        path(shift("M548 262 C564 270 586 272 606 264 C604 276 596 284 586 286 C568 288 554 280 546 268 Z", dx, dy), "#5a2630"),
        path(shift("M530 266 C544 282 566 290 590 286 C598 284 603 278 604 272 C606 284 598 300 580 306 C560 310 540 304 528 290 C524 282 525 272 530 266 Z", dx, dy), jaw, outline, 7),
        path(shift("M562 272 C574 274 590 274 600 270 C608 276 610 290 604 298 C597 303 589 298 588 288 C580 286 570 282 562 276 Z", dx, dy), "#ec8a93", "#7a3340", 4),
        line(shift("M574 277 C584 279 593 282 598 290", dx, dy), "#c9606e", 3),
    ]


# ---------------------------------------------------------------------------
# Honey
# ---------------------------------------------------------------------------

HONEY: Palette = {
    "outline": "#3a241c", "coat": "#cb7a34", "coat_light": "#e09a4e", "coat_dark": "#a45d26",
    "far_upper": "#8f5226", "far_lower": "#a8632d", "far_light": "#c07f42", "far_paw": "#c98a48",
    "leg": "#d48a40", "leg_light": "#e8a85c", "paw": "#e6aa62", "toe": "#7a4a24",
    "cream": "#f3d9b0", "eye_rim": "#241815", "iris": "#5a3520",
}


def honey(left_side: bool = False) -> Dict[str, List[str]]:
    """Honey from her right side (she faces right, as each character is
    drawn), or from her left side. The two differ in one thing: the tip of
    her RIGHT ear has a small flap. It is her near ear from the right and
    her far ear from the left."""
    p, o = HONEY, HONEY["outline"]
    parts = legs(p)
    # A brush like a fox's: thick, rough under it, and pale on the under side.
    parts["tail-base"] = [
        path("M212 286 C190 290 176 280 166 282 C154 284 148 270 138 268 C126 264 122 250 116 240 C106 220 110 198 126 192 C144 186 156 200 162 214 C172 232 190 238 216 238 Z", p["coat"], o, 8),
        line("M204 278 C184 280 160 268 142 250 C132 240 126 228 124 216", "#f0c48a", 9),
        line("M196 246 C178 240 162 226 154 210", p["coat_light"], 6),
    ]
    parts["tail-tip"] = [
        path("M134 216 C108 196 96 164 108 140 C116 124 138 124 150 138 C164 156 168 188 160 218 C155 230 142 228 134 216 Z", p["coat"], o, 8),
        line("M116 152 C118 172 126 192 138 208", "#f0c48a", 9),
        line("M138 142 C148 158 152 180 150 204", p["coat_light"], 6),
    ]
    # A round, well-fed body. The belly is a paler orange, not white.
    parts["body"] = [
        path("M194 245 C214 214 250 199 291 204 C326 206 349 216 382 213 C422 205 460 218 477 250 C490 276 479 318 455 334 C427 350 394 341 366 339 C326 337 285 355 242 347 C205 338 180 300 194 245 Z", p["coat"], o, 9),
        path("M205 257 C217 230 248 216 280 216 C260 229 252 247 247 267 C238 295 228 309 211 305 C197 294 198 274 205 257 Z", p["coat_light"]),
        path("M325 222 C345 231 367 236 393 226 C426 214 451 227 464 252 C465 277 452 293 431 305 C401 311 376 294 350 286 C333 270 325 246 325 222 Z", p["coat_light"]),
        path("M271 319 C315 331 344 311 377 316 C400 323 425 329 451 314 C433 346 406 345 373 337 C325 331 293 357 251 343 Z", "#eab878"),
        line("M199 270 C202 239 225 219 251 211", "#eeb46a", 7),
    ]
    # A thick neck, a paler throat, and a small white patch low on the chest.
    parts["neck"] = [
        path("M425 224 C452 200 486 203 507 227 L501 293 C481 320 455 335 435 331 C451 296 447 255 425 224 Z", p["coat"], o, 8),
        path(NECK_FRONT, "#e6a65c"),
        path("M462 292 C472 285 487 287 493 296 C489 311 474 323 459 322 C462 312 463 302 462 292 Z", "#fbf3e4"),
    ]
    # Very large ears: a dark edge, the coat inside it, and a dull pink
    # middle with a tuft of pale fur at the root.
    ear_edge = "M452 200 C442 160 444 120 462 84 C467 74 477 74 483 83 C500 114 512 146 516 178 C501 193 474 201 452 200 Z"
    ear_coat = "M459 194 C452 160 454 124 468 96 C482 122 494 150 503 176 C492 186 474 194 459 194 Z"
    ear_pink = "M468 186 C463 158 464 132 471 112 C483 134 492 154 496 172 C488 180 478 185 468 186 Z"
    ear_tuft = "M466 186 C470 172 478 164 488 160 C490 168 492 174 494 178 C486 184 476 187 466 186 Z"
    # The ear with the flap: it stops at a fold, a little under where the
    # other ear has its tip. The tip flops OUTWARD, to her right, away from
    # the middle of her head (Jon, 2026-10-13, of a tip drawn to the side:
    # "it looks like it is flopping inward instead of outward"). Side on,
    # outward is toward the viewer or away, not left or right:
    # * seen from her right, the ear is the near one and the tip comes
    #   toward the viewer: a small piece that hangs DOWN over the face of
    #   the ear, with the back of the ear showing;
    # * seen from her left, the ear is the far one and the tip goes away
    #   from the viewer: the ear ends in a round fold, and no piece hangs.
    flap_edge = "M452 200 C443 162 444 124 460 92 L486 84 C500 114 512 146 516 178 C501 193 474 201 452 200 Z"
    flap_coat = "M459 194 C453 162 454 128 466 102 L482 97 C493 124 500 150 503 176 C492 186 474 194 459 194 Z"
    flap_pink = "M468 186 C463 160 464 136 470 116 L478 113 C486 134 493 154 496 172 C488 180 478 185 468 186 Z"
    flap_tip = "M458 93 C466 86 477 82 488 82 C489 95 484 110 474 121 C466 114 460 104 458 93 Z"
    flap_crease = "M462 93 C469 89 478 86 485 85"
    # The far ear's fold: its top is round, with the edge of the fold on it.
    fold_edge = "M452 200 C443 164 444 128 458 98 C464 86 482 80 489 90 C501 118 512 148 516 178 C501 193 474 201 452 200 Z"
    fold_rim = "M460 99 C467 90 480 86 487 93"

    def ear(flap: bool, far: bool) -> List[str]:
        """One of her ears. The far ear is behind the head: darker, and moved."""
        dx, dy = (40, 6) if far else (0, 0)
        edge, pink = ("#6b3a1a", "#a87a70") if far else ("#74401c", "#c99488")
        coat = "#9c5825" if far else "#b96a2b"
        if not flap:
            shapes = (ear_edge, ear_coat, ear_pink)
        else:
            shapes = (fold_edge if far else flap_edge, flap_coat, flap_pink)
        out = [path(shift(shapes[0], dx, dy), edge, o, 8), path(shift(shapes[1], dx, dy), coat), path(shift(shapes[2], dx, dy), pink)]
        if not far:
            out.append(path(ear_tuft, "#f0cfa6"))
        if flap and far:
            out.append(line(shift(fold_rim, dx, dy), "#c98a4a", 4))
        elif flap:
            out.append(path(flap_tip, "#a35e27", o, 6))
            out.append(line(flap_crease, "#f0b46a", 3))
        return out

    nose = shift(NOSE, -8, 2)
    parts["head"] = [
        # Her far ear: her left ear from the right, her right ear from the left.
        *ear(flap=left_side, far=True),
        path(SKULL, p["coat"], o, 9),
        path("M500 172 C517 161 543 164 556 180 C546 179 537 188 533 201 C519 198 508 188 500 172 Z", p["coat_light"]),
        # The fur about the eye is pale, and the brow has gone grey.
        path("M496 216 C502 204 520 201 531 210 C536 221 533 234 524 240 C511 242 500 236 496 224 Z", "#e9ad68"),
        # The pip of the eyebrow: a pale mark over the eye.
        path(BROW_PIP, "#f6dcae", "#b46a2c", 2.5),
        path("M468 246 C482 234 506 238 520 252 C512 268 492 274 476 266 Z", "#e2a25a"),
        # A short muzzle like a fox's. It is grey about the nose and the lips.
        path("M542 220 C560 210 580 212 598 222 C610 229 614 243 609 255 C602 266 578 268 556 265 L533 251 C529 237 533 226 542 220 Z", p["coat_light"], o, 8),
        path("M572 226 C584 221 598 225 606 235 C610 245 608 254 603 259 C591 265 575 265 563 261 C561 248 564 235 572 226 Z", "#ebe5dc"),
        path("M564 250 C575 256 591 258 603 253 C599 261 584 265 567 261 Z", "#cfc8be"),
        line("M556 260 C572 267 594 265 603 256", "#5a3a2a", 5),
        path(nose, "#201c1d", "#121011", 4),
        line("M593 222 C598 221 602 224 603 227", "#7d777a", 3),
    ]
    parts.update(eyes(p, at=(514.0, 225.0), size=1.22))
    parts["rest-mouth"] = mouth("#ece6dc", o, -8, -2)
    parts["bark-mouth"] = bark_mouth("#ece6dc", o, -8, -2)
    parts["ear"] = [
        *ear(flap=not left_side, far=False),
    ]
    return parts


# ---------------------------------------------------------------------------
# Roadie
# ---------------------------------------------------------------------------

ROADIE: Palette = {
    "outline": "#33292a", "coat": "#d39a5c", "coat_light": "#e8b97e", "coat_dark": "#a8713d",
    "far_upper": "#8f6a47", "far_lower": "#a67a4f", "far_light": "#c29a6c", "far_paw": "#dcc6a2",
    "leg": "#dba663", "leg_light": "#f0c68c", "paw": "#f3e3c4", "toe": "#a07848",
    "cream": "#f4e6cb", "eye_rim": "#2a1e1c", "iris": "#5a3a22",
    "saddle": "#65717e", "saddle_light": "#8a97a4", "saddle_dark": "#47515d", "fleck": "#c6ced6",
}

# Flecks of the saddle: (x, y, radius, light).
ROADIE_FLECKS = [
    (232, 244, 5, 1), (250, 228, 4, 0), (262, 262, 6, 1), (280, 238, 4, 1), (296, 276, 5, 0),
    (306, 226, 5, 1), (322, 254, 6, 1), (338, 232, 4, 0), (346, 278, 5, 1), (362, 246, 5, 1),
    (378, 268, 4, 0), (388, 232, 5, 1), (404, 254, 5, 1), (416, 232, 3, 0), (244, 284, 4, 1),
    (274, 290, 4, 0), (318, 286, 4, 1), (396, 282, 4, 1), (222, 268, 4, 0), (356, 222, 3, 1),
]


def roadie() -> Dict[str, List[str]]:
    p, o = ROADIE, ROADIE["outline"]
    parts = legs(p)
    # Grey ticking on the haunch and the shoulder.
    parts["near-hind-upper"] += [
        path("M250 296 C272 290 292 304 298 326 C282 322 262 320 242 326 C242 314 245 303 250 296 Z", p["saddle"]),
        *[f'<circle cx="{x}" cy="{y}" r="{r}" fill="{p["fleck"]}"/>' for x, y, r in ((262, 308, 4), (280, 314, 3), (268, 342, 3), (286, 348, 3))],
    ]
    parts["near-fore-lower"] += [f'<circle cx="{x}" cy="{y}" r="2.6" fill="{p["cream"]}"/>' for x, y in ((424, 400), (410, 424), (426, 440))]
    parts["near-hind-lower"] += [f'<circle cx="{x}" cy="{y}" r="2.6" fill="{p["cream"]}"/>' for x, y in ((284, 384), (270, 412), (262, 438))]
    # A brush of a tail: a rough under edge, and a white end.
    parts["tail-base"] = [
        path("M210 282 C196 285 188 277 180 280 C171 283 166 272 158 272 C148 273 144 260 136 258 C126 255 124 243 120 234 C112 216 116 202 129 197 C144 191 154 203 160 215 C171 234 188 240 214 240 Z", p["saddle"], o, 8),
        line("M192 250 C172 244 154 228 146 210", p["saddle_light"], 7),
        *[f'<circle cx="{x}" cy="{y}" r="3" fill="{p["fleck"]}"/>' for x, y in ((176, 258), (158, 244), (140, 226))],
    ]
    parts["tail-tip"] = [
        path("M136 214 C112 192 103 160 115 140 C124 127 143 129 153 142 C163 158 165 186 158 216 C153 228 142 226 136 214 Z", "#f6f3ec", o, 8),
        path("M137 212 C128 204 124 196 122 188 C134 190 148 192 160 190 C160 200 159 208 157 216 C152 226 142 224 137 212 Z", p["saddle_light"]),
        line("M124 150 C130 140 142 140 148 150", "#ffffff", 5),
    ]
    parts["body"] = [
        # The biggest of the three: a deep body.
        path("M194 245 C214 214 250 199 291 204 C326 206 349 216 382 213 C422 205 460 218 477 250 C490 276 479 318 455 334 C427 350 394 341 366 339 C326 337 285 355 242 347 C205 338 180 300 194 245 Z", p["coat"], o, 9),
        path("M271 319 C315 331 344 311 377 316 C400 323 425 329 451 314 C433 346 406 345 373 337 C325 331 293 357 251 343 Z", p["cream"]),
        # The saddle: from behind the shoulder to the root of the tail.
        path("M203 250 C220 220 252 206 291 210 C326 212 349 222 382 219 C402 216 420 218 434 226 C440 250 432 276 414 292 C386 304 356 298 330 296 C296 294 262 310 228 304 C206 292 196 270 203 250 Z", p["saddle"]),
        path("M228 304 C262 310 296 294 330 296 C356 298 386 304 414 292 C398 306 372 310 346 306 C312 302 276 320 244 314 Z", p["saddle_dark"]),
        *[f'<circle cx="{x}" cy="{y}" r="{r}" fill="{p["fleck"] if light else p["saddle_dark"]}"/>' for x, y, r, light in ROADIE_FLECKS],
        line("M214 246 C226 226 250 216 276 214", p["saddle_light"], 6),
        line("M436 228 C456 234 470 248 476 268", "#f0c890", 7),
    ]
    parts["neck"] = [
        path(NECK, p["coat"], o, 8),
        path(NECK_FRONT, p["cream"]),
        # The ruff: the fur of the neck stands out over the chest.
        path("M436 300 L452 306 L450 318 L466 314 L468 326 L482 314 L488 322 L494 300 C482 312 458 316 436 300 Z", p["cream"], o, 6),
        path(COLLAR, "#e2622b", "#8f3915", 5),
        f'<circle cx="476" cy="298" r="6" fill="#d9dde0" stroke="#6b7278" stroke-width="4"/>',
    ]
    ear_outer = "M458 198 C452 164 454 132 467 104 C471 96 479 96 484 103 C497 126 507 150 511 178 C498 191 475 199 458 198 Z"
    ear_inner = "M469 185 C465 160 466 138 473 120 C484 138 493 156 497 174 C488 181 478 185 469 185 Z"
    parts["head"] = [
        path(shift(ear_outer, 36, 6), p["coat_dark"], o, 8),
        path(shift(ear_inner, 36, 6), "#b98c6c"),
        path(SKULL, p["coat"], o, 9),
        path("M500 172 C517 161 543 164 556 180 C546 179 537 188 533 201 C519 198 508 188 500 172 Z", p["coat_light"]),
        # A grey blaze from between the ears to the brow.
        path("M486 170 C500 162 516 160 530 163 C528 176 522 190 512 200 C500 196 490 184 486 170 Z", "#8d8478"),
        f'<circle cx="504" cy="176" r="3" fill="{p["fleck"]}"/>',
        f'<circle cx="517" cy="184" r="2.6" fill="{p["fleck"]}"/>',
        path("M470 244 C484 232 508 236 522 250 C514 266 494 272 478 264 Z", "#f1d3a2"),
        path(MUZZLE, "#f6e6c6", o, 8),
        line("M548 223 C563 218 584 222 596 232", "#fff6e2", 7),
        line("M562 262 C579 269 602 266 611 256", "#93683f", 5),
        line("M486 212 C500 202 517 205 526 216", "#6e4a2b", 6),
        path(NOSE, "#262528", "#18171a", 4),
        line("M601 220 C606 219 610 222 611 225", "#827c80", 3),
    ]
    parts.update(eyes(p))
    parts["rest-mouth"] = mouth("#f6e8cd", o)
    parts["bark-mouth"] = bark_mouth("#f6e8cd", o)
    parts["ear"] = [
        path(ear_outer, "#c98f55", o, 8),
        path(ear_inner, "#efc9a6"),
        # The edge of the ear is dark.
        line("M462 190 C458 162 460 136 470 112", "#7c5a3c", 5),
    ]
    return parts


# ---------------------------------------------------------------------------
# Bezoar
# ---------------------------------------------------------------------------

# Her coat is close to Honey's, and a little more tan (Jon, 2026-10-13).
BEZOAR: Palette = {
    "outline": "#38251f", "coat": "#c98444", "coat_light": "#dd9f5c", "coat_dark": "#a5672f",
    "far_upper": "#8c5628", "far_lower": "#a36632", "far_light": "#bb8248", "far_paw": "#cf9c64",
    "leg": "#d28d4c", "leg_light": "#e6aa68", "paw": "#ebc490", "toe": "#8f5c2e",
    "cream": "#f2d6a6", "eye_rim": "#1f1513", "iris": "#5b3a22",
}

def bezoar() -> Dict[str, List[str]]:
    p, o = BEZOAR, BEZOAR["outline"]
    parts = legs(p)
    # A long thin tail with a dark end.
    parts["tail-base"] = [
        path("M207 268 C176 263 150 248 136 222 C132 212 134 205 141 203 C149 201 153 208 157 218 C168 236 186 243 213 247 Z", p["coat"], o, 8),
        line("M190 249 C172 244 156 230 150 214", p["coat_light"], 5),
    ]
    parts["tail-tip"] = [
        path("M140 211 C128 192 124 172 130 157 C134 150 142 151 146 158 C150 170 151 188 150 212 C147 220 143 219 140 211 Z", "#6b5145", o, 8),
    ]
    # Lanky: a chest that is not deep, and a belly that goes up to a narrow waist.
    parts["body"] = [
        path("M198 245 C218 218 250 203 291 207 C326 209 349 218 382 215 C420 208 455 220 472 250 C484 272 476 310 454 324 C430 336 400 326 370 316 C332 304 290 322 250 320 C214 316 186 298 198 245 Z", p["coat"], o, 9),
        path("M207 256 C219 231 248 218 280 218 C261 230 253 246 248 264 C240 288 230 300 214 297 C201 288 201 271 207 256 Z", p["coat_light"]),
        path("M325 223 C345 232 367 236 393 227 C426 216 449 228 462 252 C463 274 451 288 431 298 C402 304 377 290 351 282 C334 268 325 246 325 223 Z", p["coat_light"]),
        path("M292 306 C322 304 346 294 374 300 C398 308 426 316 448 306 C432 328 404 326 372 314 C332 302 298 322 266 318 Z", p["cream"]),
        line("M400 240 C410 256 412 278 406 296", p["coat_dark"], 4),
        line("M238 252 C231 268 232 286 240 300", p["coat_dark"], 4),
        line("M201 268 C204 240 226 221 251 213", "#eeb878", 6),
    ]
    parts["neck"] = [
        path("M431 228 C454 208 482 210 500 228 L495 286 C479 308 458 322 441 320 C454 290 450 254 431 228 Z", p["coat"], o, 8),
        path("M459 232 C472 231 486 238 495 253 L490 286 C480 304 463 316 450 313 C466 290 468 256 459 232 Z", p["cream"]),
        # The collar: brown, with a row of marks, a brass tag and a blue bone.
        path("M447 266 C462 276 481 276 497 264 L495 283 C481 294 462 294 449 287 Z", "#6e4129", "#3a2116", 5),
        line("M457 279 L463 284 L469 279 M475 280 L481 284 L487 278", "#e0b34f", 3),
        f'<circle cx="464" cy="300" r="7" fill="#c9a44a" stroke="#6f5a22" stroke-width="4"/>',
        path("M474 297 C470 293 474 288 478 291 L490 299 C494 296 499 300 496 304 C500 307 496 312 492 309 L480 301 C477 304 472 301 474 297 Z", "#3aa0e0", "#1e5f8c", 3),
    ]
    # Two ears with a SLIGHT flop (Jon, 2026-10-13: "having the two flop ears
    # for beazor was correct", "slight flops"): each stands up tall, and only
    # its end hangs forward. The ear is of the coat; only its tip is dark
    # ("Her ears only have the dark tips").
    ear_edge = "M456 199 C448 166 449 132 461 102 L490 96 C502 124 510 152 513 178 C499 192 474 200 456 199 Z"
    ear_inner = "M467 187 C462 162 463 140 469 120 L486 116 C493 138 498 158 500 176 C490 182 478 186 467 187 Z"
    ear_tip = "M459 104 C468 90 483 86 494 91 C506 98 516 110 519 124 C506 121 488 116 463 116 C459 112 458 108 459 104 Z"
    parts["head"] = [
        path(shift(ear_edge, 42, 8), p["coat_dark"], o, 8),
        path(shift(ear_inner, 42, 8), "#b98a6a"),
        path(shift(ear_tip, 42, 8), "#3f2f2a", o, 7),
        path(SKULL, p["coat"], o, 9),
        path("M500 172 C517 161 543 164 556 180 C546 179 537 188 533 201 C519 198 508 188 500 172 Z", p["coat_light"]),
        # The muzzle is of the coat at its root and goes dark toward the nose,
        # in three steps, so the dark blends in (Jon, 2026-10-13: "her muzzle
        # isn't that dark. It is towards the end, but it sort of blends in").
        path(MUZZLE, "#b97a40"),
        path("M560 214 C574 210 592 214 604 221 C616 229 620 244 616 256 C608 266 584 268 566 266 C561 250 558 232 560 214 Z", "#8f5d3a"),
        path("M584 216 C596 216 608 222 614 230 C619 240 618 250 614 256 C606 264 594 266 584 265 C580 250 581 232 584 216 Z", "#5c3d31"),
        path(MUZZLE, "none", o, 8),
        line("M548 223 C560 219 572 219 582 222", "#d09a5e", 5),
        line("M562 262 C579 269 602 266 611 256", "#3a2620", 5),
        # The pip of the eyebrow: a dark mark over the eye.
        path(shift(BROW_PIP, 0, -3), "#33231d", "#33231d", 2),
        path(NOSE, "#1b1718", "#0e0c0d", 4),
        line("M601 220 C606 219 610 222 611 225", "#6f686b", 3),
    ]
    parts.update(eyes(p, size=1.12))
    parts["rest-mouth"] = mouth("#8f5d3a", o)
    parts["bark-mouth"] = bark_mouth("#8f5d3a", o)
    parts["ear"] = [
        path(ear_edge, "#b9783c", o, 8),
        path(ear_inner, "#e2b48c"),
        path(ear_tip, "#4c3932", o, 7),
    ]
    return parts


# ---------------------------------------------------------------------------

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
    ("neck", "Neck and Collar", "neck", "body", 38),
    ("rest-mouth", "Mouth - At Rest", "rest_mouth", "head", 39),
    ("bark-mouth", "Mouth - Bark", "bark_mouth", "head", 39),
    ("head", "Head and Muzzle", "head", "head", 40),
    ("eye-open", "Eye - Open", "eye_open", "head", 41),
    ("eye-x", "Eye - Death X", "eye_x", "head", 41),
    ("eye-happy", "Eye - Happy (closed)", "eye_happy", "head", 41),
    ("ear", "Ear", "ear", "ear", 42),
]

#: name -> its drawings: (the name of the SVG, the label of the view, the drawing).
DOGS: Dict[str, list] = {
    "dog_honey": [
        ("dog_honey_side", "Honey - Side Right", honey),
        (LEFT_SIDE["dog_honey"], "Honey - Left Side", lambda: honey(left_side=True)),
    ],
    "dog_roadie": [("dog_roadie_side", "Roadie - Side Right", roadie)],
    "dog_bezoar": [("dog_bezoar_side", "Bezoar - Side Right", bezoar)],
}


def svg(name: str, svg_name: str, view: str, draw: Callable[[], Dict[str, List[str]]]) -> str:
    parts = draw()
    fit_legs(parts, LEG_SCALE[name], LEG_THICKNESS[name])
    missing = [group for group, *_ in LAYERS if group not in parts]
    if missing:
        raise RuntimeError(f"{name} has no drawing for: {', '.join(missing)}")
    groups = "\n".join(layer(group, label, part, bone, z, parts[group]) for group, label, part, bone, z in LAYERS)
    slug = svg_name.replace("_", "-")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg"\n'
        '     xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"\n'
        '     width="640mm" height="512mm" viewBox="0 0 640 512"\n'
        f'     data-character-design="{slug}-v1">\n'
        f'  <g id="{slug}" inkscape:groupmode="layer" inkscape:label="{view}">\n'
        f"{groups}\n"
        "  </g>\n"
        "</svg>\n"
    )


def main() -> None:
    for name, drawings in DOGS.items():
        for svg_name, view, draw in drawings:
            out = DATA / name / f"{svg_name}.svg"
            out.parent.mkdir(parents=True, exist_ok=True)
            tmp = out.with_suffix(".svg.tmp")
            tmp.write_text(svg(name, svg_name, view, draw), encoding="utf8")
            tmp.replace(out)
            print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
