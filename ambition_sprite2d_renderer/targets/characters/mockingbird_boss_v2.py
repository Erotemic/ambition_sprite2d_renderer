"""SVG-rigged sprite target for the Mockingbird v2: the boss redrawn as a mechanical predator.

A CANDIDATE redesign (Jon, 2026-10-06), after the mechanical "mockingbird"
of the How to Kill a Mockingbird Flash animation: a lean black skull with a
tall forehead, an overhanging brow, a glowing slit eye and a long hooked beak
of fangs on a segmented steel neck; a cage of steel ribs round a glowing red
engine-heart; two armoured wings swept back over the hull, a missile slung
under each; two rotors on tall masts; a heavy thruster at the tail; two
grappling claws beneath. Jon's first review: "the head is too chunky ... It
should be sleek and mean. It can have a big forehead"; wings "are
important", with the missiles on them; the rotors raised clear of the spikes. The first design (``mockingbird_boss``, a nested
scene-graph rig) stays published beside it as its lineage; the game still
wears the first.

The SVG ``data/characters/mockingbird_boss_v2/mockingbird_boss_v2.svg`` owns
the art and marks every joint. The rig document
``rigged/mockingbird_boss_v2/mockingbird_boss_v2_side.rig.json`` owns the
skeleton and the clips; ``scripts/build_mockingbird_boss_v2_rig.py`` derives
it from the SVG and authors the clips, keying the swap sets (eye state, each
rotor's spin state, each claw open or shut) and each effect's strength
(``fx.*``). This module owns only the effects and publication.

The rows are the first sheet's six (``rest``, ``thrust``, ``bite``, ``slash``,
``hit``, ``death``) with its frame counts and durations. Drawn facing RIGHT,
where the first sheet faced left.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from PIL import Image

from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.sheet_build import build_sheet
from . import _creature_fx as FX
from ._svg_fighter_effects import FxCanvas, compose_rig_frame

Point = Tuple[float, float]

TARGET_NAME = "mockingbird_boss_v2"
SHEET_FILES = [
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
]
RIG_PATH = Path(__file__).resolve().parent / "rigged" / TARGET_NAME / "mockingbird_boss_v2_side.rig.json"
FRAME_SIZE = (570, 380)
#: Sprite pixels per SVG unit (the rig's ``svg_source.scale``).
ART_SCALE = 0.5
#: The art script draws in design units shifted by this much.
DX, DY = 120.0, 130.0


def S(x: float, y: float) -> Point:
    """A design point of the art script as an SVG point."""
    return (x + DX, y + DY)


def _px(x: float, y: float) -> Dict[str, float]:
    """A design point as a sprite-frame point."""
    sx, sy = S(x, y)
    return {"x": round(sx * ART_SCALE, 1), "y": round(sy * ART_SCALE, 1)}


ACTOR_METADATA = {
    "authoring_description": (
        "The Mockingbird v2 adapts the mechanical creature of the old How to Kill a Mockingbird "
        "Flash animation into a giant predator-gunship that mimics the fighters it hunts: a lean "
        "black beaked skull with a glowing slit eye and fangs on a steel neck, a rib cage round a "
        "glowing engine-heart, armoured wings carrying missiles, rotors, a thruster and two "
        "grappling claws."
    ),
    "gameplay_description": (
        "Use as a multipart aerial mimic boss. Its copied attacks should be recognizable "
        "but imperfectly timed, leaving a novelty gap where the player can escape or counter."
    ),
    "actor": {"character_id": f"npc_{TARGET_NAME}", "display_name": "The Mockingbird"},
    "body": {
        "body_plan": "BossMultipart",
        "body_kind": "Wide",
        "traits": ["boss", "multipart", "aerial", "machine", "svg_rigged"],
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "animation_bindings": {
        "default": {"animation": "rest", "events": []},
        "locomotion.fly": {"animation": "thrust", "events": []},
    },
    # Points on the drawn frame, at rest.
    "sockets": {
        "mouth": {"source": "mockingbird_boss_v2.geometry", "point": _px(880.0, 234.0)},
        "head": {"source": "mockingbird_boss_v2.geometry", "point": _px(770.0, 160.0)},
        "core": {"source": "mockingbird_boss_v2.geometry", "point": _px(432.0, 238.0)},
        "missile": {"source": "mockingbird_boss_v2.geometry", "point": _px(622.0, 184.0)},
        "thruster": {"source": "mockingbird_boss_v2.geometry", "point": _px(114.0, 236.0)},
        "near_claw": {"source": "mockingbird_boss_v2.geometry", "point": _px(600.0, 392.0)},
    },
    "visual": {
        "default_pose": "rest",
        "canonical_source": "ambition_sprite2d_renderer/data/characters/mockingbird_boss_v2/mockingbird_boss_v2.svg",
    },
    "tags": ["boss", "multipart", "aerial", "machine", "svg_rigged"],
}


def _doc():
    return FX.rig_document(RIG_PATH)


ROWS: List[Tuple[str, int, int]] = _doc().rows()

# --- Effect glyphs, in SVG units like the art -------------------------------------

JET_LAYERS = (
    ((214, 64, 24, 170), 1.0, 1.0),
    ((255, 132, 44, 215), 0.78, 0.72),
    ((255, 214, 120, 240), 0.52, 0.46),
    ((255, 250, 228, 255), 0.26, 0.24),
)


def _jet(length: float, width: float, flicker: int):
    """Thruster exhaust along +x from the nozzle: a broad hot plume narrowing
    to a ragged tip, with shock diamonds in its core."""
    lick = (1.0, 0.88, 1.1)[flicker]
    sway = (0.0, 0.12, -0.1)[flicker]

    def paint(c: FxCanvas) -> None:
        for color, kl, kw in JET_LAYERS:
            L, w = length * kl * lick, width * kw
            pts = [(-6.0, -w * 0.5), (0.25 * L, -w * 0.46), (0.6 * L, (-0.3 + sway * 0.4) * w), (L, sway * w),
                   (0.62 * L, (0.28 + sway * 0.4) * w), (0.25 * L, w * 0.46), (-6.0, w * 0.5)]
            c.polygon(pts, color)
        for k in range(3):
            x = length * (0.14 + 0.16 * k) * lick
            r = width * (0.16 - 0.035 * k)
            c.polygon([(x - r * 1.6, 0), (x, -r), (x + r * 1.6, 0), (x, r)], (255, 255, 244, 220))

    return paint


def _paint_blur(span: float):
    def paint(c: FxCanvas) -> None:
        c.ellipse((0, 0), span, 15.0, (196, 206, 218, 46))
        c.ellipse((0, 0), span, 15.0, None, (228, 234, 240, 110), 1.6)
        c.ellipse((0, 0), span * 0.62, 9.0, None, (228, 234, 240, 60), 1.2)

    return paint


def _paint_glow(rx: float, ry: float, color):
    r, g, b = color

    def paint(c: FxCanvas) -> None:
        for k, a in ((1.0, 26), (0.8, 34), (0.6, 42), (0.42, 50)):
            c.ellipse((0, 0), rx * k, ry * k, (r, g, b, a))

    return paint


def _paint_fireball(radius: float, tail: float = 0.0):
    def paint(c: FxCanvas) -> None:
        if tail:
            c.polygon([(0, -radius * 0.8), (-tail, -radius * 0.2), (-tail * 0.7, 0), (-tail, radius * 0.3), (0, radius * 0.8)],
                      (255, 120, 36, 170))
        c.ellipse((0, 0), radius * 1.35, radius * 1.35, (255, 110, 30, 90))
        c.ellipse((0, 0), radius, radius, (255, 120, 36, 235))
        c.ellipse((radius * 0.1, -radius * 0.05), radius * 0.7, radius * 0.7, (255, 196, 80, 245))
        c.ellipse((radius * 0.18, -radius * 0.1), radius * 0.38, radius * 0.38, (255, 250, 220, 255))

    return paint


def _paint_muzzle(c: FxCanvas) -> None:
    c.star((14, 0), 30.0, (255, 196, 80, 230), points=6, inner=0.35, rotation=0)
    c.star((12, 0), 16.0, (255, 250, 220, 255), points=6, inner=0.4, rotation=30)
    for (x, y, r) in ((-8, -16, 10.0), (-14, 12, 9.0), (-26, -2, 12.0)):
        c.ellipse((x, y), r, r * 0.8, (150, 150, 158, 150))


def _paint_smoke(c: FxCanvas) -> None:
    for (x, y, r, a) in ((-10, 4, 20, 150), (8, -6, 24, 140), (0, -20, 18, 120), (16, 10, 14, 130)):
        c.ellipse((x, y), r, r * 0.86, (74, 72, 80, a))
    for (x, y, r) in ((-4, -2, 10), (10, -12, 9)):
        c.ellipse((x, y), r, r * 0.8, (128, 124, 132, 130))


def _paint_sparks(c: FxCanvas) -> None:
    for ang, L in ((-70, 34), (-30, 42), (10, 30), (50, 38), (110, 26), (160, 34), (-120, 30)):
        r = math.radians(ang)
        c.line([(6 * math.cos(r), 6 * math.sin(r)), (L * math.cos(r), L * math.sin(r))], (255, 214, 92, 240), 2.4)
        c.line([(L * 0.6 * math.cos(r), L * 0.6 * math.sin(r)), (L * math.cos(r), L * math.sin(r))], (255, 252, 236, 255), 1.2)
    c.star((0, 0), 12.0, (255, 252, 236, 255), points=8, inner=0.4, rotation=0)


def _paint_speed(c: FxCanvas) -> None:
    for y, length in ((-90, 120), (-30, 190), (30, 150), (90, 110)):
        c.line([(0, y), (length, y)], (240, 236, 228, 110), 3.4)


_GLYPHS: Dict[str, Tuple[FX.Extent, FX.Paint]] = {**FX.COMMON}
for _k in range(3):
    _GLYPHS[f"jet{_k}"] = ((8.0, 40.0, 150.0, 40.0), _jet(120.0, 66.0, _k))
    _GLYPHS[f"boost{_k}"] = ((8.0, 46.0, 260.0, 46.0), _jet(220.0, 78.0, _k))
_GLYPHS["near_blur"] = ((212.0, 18.0, 212.0, 18.0), _paint_blur(206.0))
_GLYPHS["far_blur"] = ((166.0, 18.0, 166.0, 18.0), _paint_blur(160.0))
_GLYPHS["core_glow"] = ((190.0, 110.0, 190.0, 110.0), _paint_glow(186.0, 106.0, (255, 120, 40)))
_GLYPHS["eye_glow"] = ((44.0, 24.0, 44.0, 24.0), _paint_glow(42.0, 22.0, (255, 110, 30)))
_GLYPHS["charge_s"] = ((24.0, 24.0, 24.0, 24.0), _paint_fireball(14.0))
_GLYPHS["charge_l"] = ((36.0, 36.0, 36.0, 36.0), _paint_fireball(24.0))
_GLYPHS["spit"] = ((90.0, 44.0, 44.0, 44.0), _paint_fireball(30.0, tail=80.0))
_GLYPHS["muzzle"] = ((40.0, 32.0, 46.0, 32.0), _paint_muzzle)
_GLYPHS["smoke"] = ((32.0, 40.0, 42.0, 32.0), _paint_smoke)
_GLYPHS["sparks"] = ((44.0, 44.0, 44.0, 44.0), _paint_sparks)
_GLYPHS["speed"] = ((4.0, 96.0, 194.0, 96.0), _paint_speed)
GLYPHS = FX.Glyphs(ART_SCALE, _GLYPHS)
_place = GLYPHS.place

REST = FX.rest_frames(_doc())


def _anchor(bone: str, x: float, y: float) -> Point:
    return FX.anchor(REST, bone, S(x, y), ART_SCALE)


A = {
    "nozzle": ("engine", _anchor("engine", 112.0, 236.0)),
    "near_hub": ("near_rotor", _anchor("near_rotor", 498.0, 58.0)),
    "far_hub": ("far_rotor", _anchor("far_rotor", 332.0, 70.0)),
    "core": ("body", _anchor("body", 440.0, 236.0)),
    "eye": ("head", _anchor("head", 800.0, 151.0)),
    "throat": ("head", _anchor("head", 850.0, 232.0)),
    "spit": ("head", _anchor("head", 976.0, 238.0)),
    "muzzle": ("near_wing", _anchor("near_wing", 622.0, 184.0)),
    "snout": ("head", _anchor("head", 934.0, 238.0)),
    "spark1": ("body", _anchor("body", 520.0, 150.0)),
    "spark2": ("neck2", _anchor("neck2", 640.0, 196.0)),
    "spark3": ("body", _anchor("body", 300.0, 170.0)),
    "smoke1": ("body", _anchor("body", 470.0, 120.0)),
    "smoke2": ("engine", _anchor("engine", 240.0, 210.0)),
    "smoke3": ("body", _anchor("body", 360.0, 130.0)),
}


def _at(world, key: str) -> Tuple[Point, float]:
    bone, local = A[key]
    bw = world[bone]
    return bw.to_world(local), bw.angle - REST[bone][1]


def _behind(canvas: FxCanvas, t: float, world, params) -> None:
    step = int(round(t * 24))
    if params.get("fx.speed", 0.0) > 0.02:
        p, _turn = _at(world, "core")
        _place(canvas, "speed", (p[0] - 300 * ART_SCALE, p[1]), params["fx.speed"], degrees=0.0)
    jet = params.get("fx.jet", 0.0)
    boost = params.get("fx.boost", 0.0)
    if jet > 0.02:
        p, turn = _at(world, "nozzle")
        name = f"{'boost' if boost > 0.4 else 'jet'}{step % 3}"
        _place(canvas, name, p, min(1.0, jet + 0.2), degrees=180.0 + turn)
    if params.get("fx.blur", 0.0) > 0.02:
        p, turn = _at(world, "far_hub")
        _place(canvas, "far_blur", p, params["fx.blur"], degrees=turn)


def _front(canvas: FxCanvas, t: float, world, params) -> None:
    step = int(round(t * 24))
    glow = params.get("fx.glow", 0.0)
    if glow > 0.02:
        p, turn = _at(world, "core")
        _place(canvas, "core_glow", p, glow, degrees=turn)
    if params.get("eye.open", 0.0) > 0.5 or params.get("eye.angry", 0.0) > 0.5:
        p, turn = _at(world, "eye")
        _place(canvas, "eye_glow", p, 0.6 + 0.4 * params.get("eye.angry", 0.0), degrees=turn)
    if params.get("fx.blur", 0.0) > 0.02:
        p, turn = _at(world, "near_hub")
        _place(canvas, "near_blur", p, params["fx.blur"], degrees=turn)
    charge = params.get("fx.charge", 0.0)
    if charge > 0.02:
        p, turn = _at(world, "throat")
        _place(canvas, "charge_l" if charge > 0.6 else "charge_s", p, min(1.0, charge + 0.3), degrees=turn)
    if params.get("fx.spit", 0.0) > 0.02:
        p, turn = _at(world, "spit")
        head = world["head"]
        _place(canvas, "spit", p, params["fx.spit"], degrees=head.angle - REST["head"][1] + 0.0)
    if params.get("fx.muzzle", 0.0) > 0.02:
        p, turn = _at(world, "muzzle")
        _place(canvas, "muzzle", p, params["fx.muzzle"], degrees=turn - 3.2)
    if params.get("fx.bite", 0.0) > 0.02:
        p, turn = _at(world, "snout")
        _place(canvas, "bite", p, params["fx.bite"], degrees=turn)
    if params.get("fx.shock", 0.0) > 0.02:
        claw = world["near_claw"].to_world((0.0, 0.0))
        _place(canvas, "shock", (claw[0], claw[1] + 40 * ART_SCALE), params["fx.shock"])
        _place(canvas, "thud", (claw[0] - 20 * ART_SCALE, claw[1] + 34 * ART_SCALE), params["fx.shock"])
    spark = params.get("fx.spark", 0.0)
    if spark > 0.02:
        for k, key in enumerate(("spark1", "spark2", "spark3")):
            if (step + k) % 2 == 0 or k == 0:
                p, turn = _at(world, key)
                _place(canvas, "sparks", p, spark, degrees=30.0 * ((step + k) % 4))
    smoke = params.get("fx.smoke", 0.0)
    if smoke > 0.02:
        for k, key in enumerate(("smoke1", "smoke2", "smoke3")):
            p, _turn = _at(world, key)
            for j in range(3):
                u = (t * 1.5 + j / 3.0 + k * 0.21) % 1.0
                at = (p[0] - (30 + 60 * u) * ART_SCALE, p[1] - (20 + 140 * u) * ART_SCALE)
                _place(canvas, "smoke", at, smoke * (1.0 - 0.7 * u))


def render_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    return compose_rig_frame(_doc(), animation, frame_idx, frame_count, behind=_behind, front=_front, fx_pieces=True)


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        label_width=118,
        actor_metadata=ACTOR_METADATA,
    )
    parts = publish_rig_flipbook(TARGET_NAME, ROWS, render_frame, outputs, frame_transform, out_dir)
    keys = ("canonical", "canonical_transparent", "spritesheet", "yaml", "ron", "actor", "preview")
    return [Path(outputs[key]) for key in keys if outputs.get(key)] + list(parts.values())


__all__ = ["ACTOR_METADATA", "ROWS", "SHEET_FILES", "TARGET_NAME", "render", "render_frame"]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "generated" / TARGET_NAME,
    )
    args = parser.parse_args(argv)
    for path in render(args.out_dir):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
