#!/usr/bin/env python3
"""Draw the spectral wolf of Castle Godwin (the Evil dimension).

    uv run python scripts/svg_art/evil_spectral_wolf_art.py
    uv run python scripts/build_evil_spectral_wolf_rig.py

Writes ``data/characters/evil_spectral_wolf/evil_spectral_wolf_side.svg``.

Jon, 2026-10-22: "I want you to create spectral wolf enemies", its ghost fire
"Red, like the Inugami". A dog the regime kept, dead and risen as a spirit:
the attack hound's body (``evil_attack_hound_art.hound``) made a wolf (a
heavy ruff, a bushy tail, a longer muzzle) and drawn in the Inugami's spirit
ink (``wolfenstein_inugami.SPIRIT``): rose fur, a maroon outline, pale gold
eyes, a mouth lit from inside. Its collar is snapped: what is left of it
hangs from its neck with the regime's tag. Ghost fire streams up off its
hackles, its back and the tip of its tail.

The joints are the hound's (so its bones are the companion dog's, as the
hound's are). The ghost fire is part of the drawing, on the bone it comes
off. The game fades it between its attacks; its rows draw that fade
(``targets/characters/evil_spectral_wolf.py``).

Drawn side on, facing right, in SVG units of 640 x 512. NO drop shadow.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for entry in (ROOT, HERE):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

import evil_attack_hound_art as H  # noqa: E402
from house_dogs_art import layer, line, path  # noqa: E402

NAME = "evil_spectral_wolf"
SVG_NAME = f"{NAME}_side"
VIEW = "Spectral Wolf - Side Right"
OUT = ROOT / "ambition_sprite2d_renderer" / "data" / "characters" / NAME / f"{SVG_NAME}.svg"

#: The hound's joints: the rig is built about them.
LEG_SCALE = H.LEG_SCALE
LEG_THICKNESS = H.LEG_THICKNESS
JAW_HINGE = H.JAW_HINGE
HEAD_PIVOT = H.HEAD_PIVOT

#: The spirit ink: the Inugami's (``wolfenstein_inugami.SPIRIT``).
INK = "#3a0816"
FUR = "#ec8084"
FUR_DARK = "#c44658"
FUR_DEEP = "#7a1832"
FUR_LIGHT = "#ffd6ce"
EYE = "#fff6c8"
EYE_POINT = "#28000a"
MOUTH = "#3c0614"
GUM = "#ff965a"
TONGUE = "#ffc478"
TOOTH = "#fff0e8"
#: Its ghost fire: the Inugami's (``wolfenstein.GHOST_*``).
FIRE_OUT = "#c41c34"
FIRE_MID = "#ff605c"
FIRE_CORE = "#ffe2d6"

#: Every colour of the hound's drawing, and its colour in the spirit ink.
RECOLOUR: Dict[str, str] = {
    H.P["outline"]: INK,
    H.P["coat"]: FUR_DARK, H.P["coat_light"]: FUR, H.P["coat_dark"]: FUR_DEEP,
    H.P["tan"]: FUR, H.P["tan_light"]: FUR_LIGHT, H.P["tan_dark"]: FUR_DARK,
    H.P["far_upper"]: FUR_DEEP, H.P["far_lower"]: FUR_DEEP, H.P["far_light"]: FUR_DARK, H.P["far_paw"]: FUR_DEEP,
    H.P["leg"]: FUR, H.P["leg_light"]: FUR_LIGHT, H.P["paw"]: FUR, H.P["toe"]: FUR_DEEP,
    H.P["cream"]: FUR_LIGHT, H.P["eye_rim"]: EYE_POINT,
    H.TOOTH: TOOTH, H.TOOTH_LINE: FUR_DARK, H.GUM: GUM, H.MOUTH: MOUTH, H.TONGUE: TONGUE,
    # The colours the hound's drawing writes as they are.
    "#151112": FUR_DEEP, "#3d2723": GUM, "#5a3a33": GUM, "#0b0809": INK, "#050404": INK, "#5b5458": FUR,
    "#100b0c": INK, "#4a1a24": FUR_DEEP, "#e8a51c": EYE, "#0b0708": EYE_POINT, "#fff6d8": "#ffffff",
    "#2a2427": FUR_DEEP, "#d9d2c6": FIRE_CORE,
}


def recolour(elements: List[str]) -> List[str]:
    """``elements`` in the spirit ink: every colour of the hound's drawing to its own."""
    table = {key.lower(): value for key, value in RECOLOUR.items()}

    def swap(match: "re.Match[str]") -> str:
        return table.get(match.group(0).lower(), match.group(0))

    return [re.sub(r"#[0-9a-fA-F]{6}", swap, element) for element in elements]


def flame(root: Tuple[float, float], length: float, width: float, lean: float, alpha: float = 0.85) -> List[str]:
    """A tongue of ghost fire up from ``root``: ``length`` long, ``width``
    wide at its root, its tip ``lean`` units to the back (negative x). Three
    layers: the red outside, the bright middle, the pale core."""
    x, y = root
    out = []
    for scale, colour, a in ((1.0, FIRE_OUT, alpha * 0.85), (0.62, FIRE_MID, alpha * 0.9), (0.3, FIRE_CORE, alpha)):
        w, h = width * scale * 0.5, length * (0.55 + 0.45 * scale)
        tip = (x + lean * (0.6 + 0.4 * scale), y - h)
        # A belly wider than its root, then a lick up to the tip.
        d = (
            f"M{x - w:.1f} {y:.1f} C{x - w * 1.6:.1f} {y - h * 0.35:.1f} {tip[0] - w * 0.9:.1f} {tip[1] + h * 0.45:.1f} {tip[0]:.1f} {tip[1]:.1f} "
            f"C{tip[0] + w * 0.5:.1f} {tip[1] + h * 0.5:.1f} {x + w * 1.5:.1f} {y - h * 0.3:.1f} {x + w:.1f} {y:.1f} Z"
        )
        out.append(path(d, colour, extra=f'fill-opacity="{a:.2f}"'))
    return out


def wolf() -> Dict[str, List[str]]:
    hound = H.hound()
    parts = {group: recolour(elements) for group, elements in hound.items()}

    # A wolf's tail: bushier than the hound's brush, and fire off its tip.
    parts["tail-base"] = recolour(hound["tail-base"]) + [
        path("M206 246 C188 236 170 224 160 208 C176 214 196 222 214 236 Z", FUR_LIGHT),
    ]
    parts["tail-tip"] = recolour(hound["tail-tip"]) + [
        path("M150 230 C128 222 108 196 98 150 C92 128 102 118 112 136 C124 160 140 190 158 210 Z", FUR_DARK, INK, 6),
        line("M108 150 C118 176 132 198 148 214", FUR, 5),
        # The tip of its tail is a plume of fire.
        *flame((104.0, 156.0), 130.0, 54.0, 60.0),
        *flame((122.0, 186.0), 96.0, 40.0, 52.0, 0.8),
        *flame((140.0, 206.0), 70.0, 30.0, 40.0, 0.7),
    ]

    # Its paws do not quite touch the world: fire licks up round them.
    for group, x in (("near-hind-paw", 300.0), ("near-fore-paw", 452.0), ("far-hind-paw", 284.0), ("far-fore-paw", 404.0)):
        parts[group] = parts[group] + [*flame((x - 14.0, 484.0), 34.0, 18.0, 14.0, 0.6), *flame((x + 8.0, 484.0), 26.0, 14.0, 10.0, 0.5)]

    # Ghost fire off its back, behind the body: it streams up and back.
    # Its cold light round it first: the glow of a spirit, not a shadow.
    parts["back-fire"] = [
        *[
            f'<ellipse cx="350" cy="244" rx="{rx}" ry="{ry}" fill="#ff605c" fill-opacity="0.05"/>'
            for rx, ry in ((250, 130), (225, 116), (200, 102), (175, 88))
        ],
        *flame((228.0, 236.0), 90.0, 44.0, 52.0, 0.8),
        *flame((272.0, 226.0), 120.0, 52.0, 62.0, 0.85),
        *flame((322.0, 222.0), 132.0, 56.0, 64.0, 0.85),
        *flame((372.0, 214.0), 118.0, 52.0, 58.0, 0.85),
    ]

    # The neck: the hound's hackles and throat, a heavy ruff over them, and
    # the snapped collar hanging under it with the regime's tag.
    neck = recolour(hound["neck"][:4])
    ruff = (
        "M372 222 C380 200 398 186 420 180 C432 166 448 160 466 162 C482 150 500 152 512 166 C522 178 524 196 518 214 "
        "C530 232 532 256 520 276 C524 296 514 316 494 326 C480 340 458 344 440 334 C424 340 404 334 396 318 "
        "C384 300 386 280 396 266 C380 258 368 240 372 222 Z"
    )
    neck += [
        path(ruff, FUR, INK, 7),
        # The tufts of the ruff.
        line("M398 268 C408 276 420 280 432 280 M404 300 C416 308 430 312 444 310 M428 326 C442 330 458 330 472 324", FUR_DARK, 4),
        line("M420 196 C432 186 448 182 462 184 M470 172 C484 168 498 170 508 178", FUR_LIGHT, 4),
        *flame((420.0, 192.0), 96.0, 40.0, 50.0, 0.8),
        *flame((462.0, 172.0), 104.0, 42.0, 52.0, 0.85),
        *flame((500.0, 166.0), 70.0, 30.0, 36.0, 0.75),
        # The snapped collar: a strip of black leather under the ruff, torn
        # at the front, the tag still on it.
        path("M452 312 C464 320 478 322 490 318 L488 330 C476 336 462 334 450 326 Z", "#151416", INK, 4),
        path("M490 318 L500 312 L496 324 L488 330 Z", "#151416", INK, 3),
        line("M454 320 C466 326 478 327 488 324", FIRE_OUT, 4),
        line("M468 330 L468 340", "#9aa0a8", 3),
        *H.regime_tag((468.0, 354.0), 13.0),
    ]
    parts["neck"] = neck

    # A longer muzzle: the head as the hound's, its nose and its teeth
    # further forward.
    parts["head"] = recolour(hound["head"]) + [
        path("M530 204 C556 192 600 196 622 206 C612 210 586 210 562 214 C548 216 536 214 530 204 Z", FUR_LIGHT),
    ]
    # Eyes that burn: the hound's almond eye, pale gold with a dark point, and
    # a glow round it.
    parts["eye-open"] = [
        '<ellipse cx="517" cy="222" rx="30" ry="18" fill="#ff605c" fill-opacity="0.35"/>',
        '<ellipse cx="517" cy="222" rx="20" ry="12" fill="#ffe2d6" fill-opacity="0.45"/>',
        *recolour(hound["eye-open"]),
    ]
    return parts


#: The hound's layers, and its ghost fire: off its back, behind the body.
LAYERS = list(H.LAYERS)
LAYERS.insert(LAYERS.index(next(entry for entry in LAYERS if entry[0] == "body")), ("back-fire", "Ghost Fire - Back", "back_fire", "body", 19))


def svg() -> str:
    parts = wolf()
    H.fit_legs(parts, LEG_SCALE, LEG_THICKNESS)
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
