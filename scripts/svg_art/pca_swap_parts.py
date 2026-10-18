#!/usr/bin/env python3
"""Draw the Perfect Cellular Automaton's swap parts and bind them to his rig.

    uv run python scripts/svg_art/pca_swap_parts.py

Jon, 2026-10-17, on the fight poses: "if you need to author new PCA parts on
the SVG to make some of these poses read well, please do that. Having
additional hand positions, and maybe torso articulations or face expressions
(with the eyes)."

The hand-drawn ``PCA-multiview.svg`` stays the art authority. This script owns
ONE layer in it, ``PCA Rig Swaps - Front Right``, and rewrites that layer
whole on every run; nothing else in the file is touched. The layer is hidden
and ``editor-only``, so Inkscape shows the drawing as it was, and a part that
names a swap group restores just that group when it rasterizes.

Each hand variant is drawn in its hand's own frame: ``u`` runs from the wrist
pivot along the hand bone's drawn rest direction, ``t`` toward the thumb. It
lands exactly where the base hand is, with the same pivot and rest angle, so
swapping it in is only a visibility change. Eye variants are drawn in place
over the base eyes, which become their own part so they can be hidden.

The second half binds the parts in ``perfect_cellular_automaton.rig.json``,
which is GUI-edited and the rig's geometry authority (its extractor is stale):
each variant becomes a part on the base part's bone, behind a channel
``<slot>.<variant>``; the base part answers ``<slot>.open`` and is visible by
default. Re-running is idempotent.
"""

from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[2]
SVG = ROOT / "assets" / "perfect-cellular-automaton" / "PCA-multiview.svg"
RIG = (ROOT / "ambition_sprite2d_renderer" / "targets" / "characters" / "rigged"
       / "perfect_cellular_automaton.rig.json")

LAYER_ID = "pca-rig-swaps"
LAYER_LABEL = "PCA Rig Swaps - Front Right"

INK = "#000000"
SKIN = "#fdedc4"
DARK = "#181715"
STROKE = 0.706
MM_PER_PX = 25.4 / 96.0  # rig pivots are document px at 96 dpi

Pt = Tuple[float, float]


def _style(fill: str, width: float = STROKE) -> str:
    return (f"fill:{fill};fill-opacity:1;stroke:{INK};stroke-width:{width};"
            "stroke-linecap:round;stroke-linejoin:miter;stroke-opacity:1")


def _poly(pid: str, pts: Sequence[Pt], fill: str) -> str:
    d = "M " + " ".join(f"{x:.3f},{y:.3f}" for x, y in pts) + " Z"
    return f'<path id="{pid}" style="{_style(fill)}" d="{d}" />'


def _line(pid: str, pts: Sequence[Pt], width: float = STROKE) -> str:
    d = "M " + " ".join(f"{x:.3f},{y:.3f}" for x, y in pts)
    return f'<path id="{pid}" style="{_style("none", width)}" d="{d}" />'


# --- hands -----------------------------------------------------------------

class HandFrame:
    """Maps hand-local (u along the bone, t toward the thumb) to document mm."""

    def __init__(self, pivot_px: Pt, rest_angle: float, thumb_sign: float):
        self.o = (pivot_px[0] * MM_PER_PX, pivot_px[1] * MM_PER_PX)
        a = math.radians(rest_angle)
        self.d = (math.cos(a), math.sin(a))
        # The thumb points toward the body: +x for the near hand, -x for the far.
        self.t = (thumb_sign * math.sin(a), -thumb_sign * math.cos(a))

    def __call__(self, pts: Iterable[Pt]) -> List[Pt]:
        return [(self.o[0] + u * self.d[0] + t * self.t[0],
                 self.o[1] + u * self.d[1] + t * self.t[1]) for u, t in pts]


CUFF = [(-1.2, -7.4), (4.6, -7.9), (5.0, 7.9), (-1.2, 7.3)]


def _fist(f: HandFrame, p: str) -> List[str]:
    """Knuckles lead along the bone; the thumb folds across the fingers."""
    return [
        _poly(f"{p}-cuff", f(CUFF), DARK),
        _poly(f"{p}-fist", f([(4.2, -7.9), (4.2, 8.0), (9.5, 9.0), (15.6, 8.3),
                              (17.4, 5.2), (17.6, -4.6), (16.0, -7.8), (9.5, -8.8)]), SKIN),
        _line(f"{p}-crease1", f([(10.6, 3.6), (16.9, 3.0)])),
        _line(f"{p}-crease2", f([(10.2, -0.4), (17.2, -0.6)])),
        _line(f"{p}-crease3", f([(10.4, -4.4), (16.8, -4.3)])),
        _poly(f"{p}-thumb", f([(5.4, 8.0), (10.8, 9.6), (14.2, 6.6), (13.4, 3.4),
                               (10.6, 4.4), (7.4, 6.0)]), SKIN),
    ]


def _palm(f: HandFrame, p: str) -> List[str]:
    """Flat open hand, fingers together and straight: the palm strike."""
    return [
        _poly(f"{p}-cuff", f(CUFF), DARK),
        _poly(f"{p}-palm", f([(4.2, -7.9), (4.2, 7.9), (13.4, 7.6), (26.2, 5.4),
                              (27.8, 2.4), (27.6, -3.6), (25.8, -6.6), (14.6, -8.2)]), SKIN),
        _line(f"{p}-sep1", f([(15.0, 3.6), (26.4, 2.6)])),
        _line(f"{p}-sep2", f([(15.2, -0.6), (27.0, -0.8)])),
        _line(f"{p}-sep3", f([(15.0, -4.6), (26.0, -4.0)])),
        _poly(f"{p}-thumb", f([(5.6, 7.8), (9.2, 12.4), (12.2, 14.6), (14.2, 13.0),
                               (11.6, 9.8), (10.4, 7.6)]), SKIN),
    ]


def _finger(base: Pt, angle: float, curl: float, l1: float, l2: float, w: float) -> List[Pt]:
    """One tapered, hooked finger as a closed polygon in hand-local coords."""
    a1, a2 = math.radians(angle), math.radians(angle + curl)
    d1, d2 = (math.cos(a1), math.sin(a1)), (math.cos(a2), math.sin(a2))
    n1, n2 = (-d1[1], d1[0]), (-d2[1], d2[0])
    k = (base[0] + d1[0] * l1, base[1] + d1[1] * l1)
    tip = (k[0] + d2[0] * l2, k[1] + d2[1] * l2)
    hw, kw, tw = w / 2.0, w * 0.45, w * 0.2
    return [
        (base[0] + n1[0] * hw, base[1] + n1[1] * hw),
        (k[0] + n1[0] * kw, k[1] + n1[1] * kw),
        (tip[0] + n2[0] * tw, tip[1] + n2[1] * tw),
        (tip[0] - n2[0] * tw, tip[1] - n2[1] * tw),
        (k[0] - n1[0] * kw, k[1] - n1[1] * kw),
        (base[0] - n1[0] * hw, base[1] - n1[1] * hw),
    ]


def _claw(f: HandFrame, p: str) -> List[str]:
    """Fingers spread and hooked: the rake."""
    out = [_poly(f"{p}-cuff", f(CUFF), DARK)]
    fingers = [((12.4, 5.2), 22.0), ((13.2, 1.7), 7.0), ((13.2, -1.9), -7.0), ((12.4, -5.4), -21.0)]
    for i, (base, ang) in enumerate(fingers):
        out.append(_poly(f"{p}-finger{i}", f(_finger(base, ang, -30.0, 6.4, 4.8, 4.0)), SKIN))
    out.append(_poly(f"{p}-palm", f([(4.2, -7.9), (4.2, 7.9), (11.8, 8.6), (14.2, 3.2),
                                     (14.2, -3.2), (12.0, -8.4)]), SKIN))
    out.append(_poly(f"{p}-thumb", f(_finger((6.4, 7.4), 58.0, -34.0, 5.8, 4.4, 4.2)), SKIN))
    return out


HAND_VARIANTS = {"fist": _fist, "palm": _palm, "claw": _claw}


# --- eyes ------------------------------------------------------------------
#
# The drawn eyes, in document mm: near (the character's right, larger) and far
# (foreshortened at the face's edge). The nose is between them, so the INNER
# corner is the near eye's right side and the far eye's left side.

def _eyes(p: str, near: Sequence[Pt], far: Sequence[Pt]) -> List[str]:
    return [_poly(f"{p}-near", near, DARK), _poly(f"{p}-far", far, DARK)]


EYE_VARIANTS = {
    # Tops slant down toward the nose.
    "fierce": lambda p: _eyes(
        p,
        [(163.60, 52.90), (163.59, 57.80), (166.96, 59.04), (166.96, 56.40)],
        [(177.70, 55.70), (177.35, 58.69), (178.79, 57.52), (179.23, 52.40)],
    ),
    # Lids lowered level: superior, unbothered.
    "smug": lambda p: _eyes(
        p,
        [(163.60, 55.20), (163.59, 57.80), (166.96, 59.04), (166.96, 56.60)],
        [(177.60, 56.00), (177.35, 58.69), (178.79, 57.52), (179.00, 55.10)],
    ),
    # Opened past the drawn size.
    "wide": lambda p: _eyes(
        p,
        [(163.20, 50.20), (163.10, 58.40), (167.40, 59.80), (167.40, 51.60)],
        [(177.80, 51.50), (177.25, 59.40), (179.05, 58.20), (179.55, 50.00)],
    ),
    # Shut in a laugh: two upturned arcs.
    "laugh": lambda p: [
        _line(f"{p}-near", [(163.30, 57.40), (165.20, 54.80), (167.20, 57.80)], 1.15),
        _line(f"{p}-far", [(177.40, 57.60), (178.40, 55.00), (179.40, 56.80)], 1.15),
    ],
}


# --- svg -------------------------------------------------------------------

def _rig() -> dict:
    return json.loads(RIG.read_text(encoding="utf8"))


def _part(rig: dict, name: str) -> dict:
    return next(p for p in rig["parts"] if p["name"] == name)


def _hand_frames(rig: dict) -> dict:
    # thumb_sign: the near (right) hand's thumb is drawn toward +x, the far toward -x.
    out = {}
    for side, sign in (("near", 1.0), ("far", -1.0)):
        part = _part(rig, f"{side}_arm_hand")
        out[side] = HandFrame(tuple(part["pivot"]), float(part["rest_angle"]), sign)
    return out


def swap_groups(rig: dict) -> List[Tuple[str, str, List[str]]]:
    """(slot, variant, svg elements) for every swap part."""
    groups = []
    for side, frame in _hand_frames(rig).items():
        for variant, draw in HAND_VARIANTS.items():
            groups.append((f"{side}_hand", variant, draw(frame, f"pca-{side}-hand-{variant}")))
    for variant, draw in EYE_VARIANTS.items():
        groups.append(("eyes", variant, draw(f"pca-eyes-{variant}")))
    return groups


def _group_id(slot: str, variant: str) -> str:
    return f"pca-swap-{slot}-{variant}".replace("_", "-")


def layer_xml(rig: dict) -> str:
    hidden = 'style="display:none" data-rig-editor-visibility="editor-only"'
    lines = [f'  <g id="{LAYER_ID}" inkscape:groupmode="layer" inkscape:label="{LAYER_LABEL}" {hidden}>']
    for slot, variant, elems in swap_groups(rig):
        gid = _group_id(slot, variant)
        lines.append(f'    <g id="{gid}" inkscape:label="{slot}: {variant}" {hidden}>')
        lines.extend(f"      {e}" for e in elems)
        lines.append("    </g>")
    lines.append("  </g>")
    return "\n".join(lines) + "\n"


def write_svg(rig: dict) -> None:
    text = SVG.read_text(encoding="utf8")
    block = layer_xml(rig)
    pattern = re.compile(rf'  <g id="{LAYER_ID}".*?\n  </g>\n', re.S)
    if pattern.search(text):
        text = pattern.sub(lambda _m: block, text, count=1)
    else:
        end = text.rindex("</svg>")
        text = text[:end] + block + text[end:]
    _atomic_write(SVG, text)


# --- rig -------------------------------------------------------------------

BASE_EYES = ["path53807", "path53809"]


def bind_rig(rig: dict) -> dict:
    parts = [p for p in rig["parts"] if not p["name"].startswith("swap.")]
    by_name = {p["name"]: p for p in parts}

    head = by_name["head"]
    if "eyes" not in by_name:
        head["include"] = [i for i in head["include"] if i not in BASE_EYES]
        eyes = {"name": "eyes", "bone": "head", "z": head["z"] + 0.5, "kind": "sprite",
                "include": list(BASE_EYES), "pivot": head["pivot"], "rest_angle": head["rest_angle"]}
        parts.insert(parts.index(head) + 1, eyes)
        by_name["eyes"] = eyes

    bases = {"near_hand": by_name["near_arm_hand"], "far_hand": by_name["far_arm_hand"],
             "eyes": by_name["eyes"]}
    for slot, base in bases.items():
        base["opacity_channel"] = f"{slot}.open"
        base["opacity_default"] = 1.0

    for slot, variant, _elems in swap_groups(rig):
        base = bases[slot]
        part = {"name": f"swap.{slot}.{variant}", "bone": base["bone"], "z": base["z"] + 0.05,
                "kind": "sprite", "include": [_group_id(slot, variant)],
                "pivot": base["pivot"], "rest_angle": base["rest_angle"],
                "opacity_channel": f"{slot}.{variant}"}
        parts.insert(parts.index(base) + 1, part)
    rig["parts"] = parts
    return rig


def _atomic_write(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf8")
    os.replace(tmp, path)


def main() -> None:
    rig = _rig()
    write_svg(rig)
    _atomic_write(RIG, json.dumps(bind_rig(rig), indent=1))
    print(f"wrote {SVG.name} layer {LAYER_LABEL!r} and bound "
          f"{len(swap_groups(rig))} swap parts in {RIG.name}")


if __name__ == "__main__":
    main()
