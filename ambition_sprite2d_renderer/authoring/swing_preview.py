"""See the swing: the character, the polygon that hurts, and the effect drawn for it.

This is the picture the authoring loop was missing. Jon, opening this campaign:

    I want it to be easy for an artist to know what hitpoly they are writing a
    sprite for. Conversely I want a really good effect to have an artist be able
    to draw a hitpoly to match it.

Both directions need the same thing on screen at once, at the size the game will
use, and until now neither was available without launching the game:
`frame_debug` draws the polygon on the character and knows nothing about the
effect, and the effect's own sheet is a square frame with no character in it.

## It reads the GENERATOR, not the published assets

Deliberately. Previewing what has already been rendered turns a five-second
question into a regenerate-and-look cycle, and an authoring loop you have to
publish into is one nobody iterates in. Editing a number in
`slash_envelope.py` and running this shows the new swing immediately, before
anything is written.

## What it reproduces, and why that matters

The runtime does not draw the effect where the polygon is. It projects the
volume into an oriented quad (`CombatVolume::swing_shape`) — origin at the
attacker, axis toward the volume, extent from its own points — and stretches the
sprite into THAT. Art can therefore be a perfect fit in its own frame and land
wrong in the game, which is exactly what happened repeatedly here: 16% of the
drawn slash outside its polygon from an authoring-space mismatch, 9% more from a
quarter-turn, 15% more from a margin applied after the projection.

So this performs the same projection rather than drawing the two shapes side by
side, and reports what fraction of the drawn effect lands outside the volume.
That number is the contract: the hitbox may overreach the effect, but nothing
drawn may fail to hit.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from PIL import Image, ImageDraw

# World units per authoring-frame pixel for the 30x48 collision body, and the
# body's own height. Both come from the runtime's sprite scaling; they are here
# so the preview places the attacker where the game does.
FRAME_SCALE = 0.50625
BODY_WORLD_H = 48.0

POLY_COLOUR = (255, 60, 160, 255)
QUAD_COLOUR = (90, 170, 255, 150)
ATTACKER_COLOUR = (120, 255, 120, 255)


def _swing_quad(poly: Sequence[Tuple[float, float]], attacker: Tuple[float, float]):
    """`CombatVolume::swing_shape`, reproduced.

    Axis from the volume's NEAREST point to the attacker toward its FARTHEST;
    `t` along it; the extent is whatever the volume's own points project to.
    Keep this in step with `ambition_geometry::swing_shape` — a preview that
    models the pipeline minus one step is a confident wrong answer, not a weaker
    one, and this file has already caught that failure once.

    ⚠ It was `attacker → centroid`, matching the runtime at the time. When the
    runtime moved (so that raising a swing to chest height stopped tilting it),
    this did not, and it promptly reported 7% of a contained slash outside its
    polygon — measuring the art against a quad the game no longer builds.
    """
    def _d2(p):
        return (p[0] - attacker[0]) ** 2 + (p[1] - attacker[1]) ** 2

    tip = max(poly, key=_d2)
    # The ROOT is the near edge's midpoint, not its nearest vertex: a symmetric
    # swing has two vertices equally near the wielder, and picking either gives
    # an axis running diagonally from a corner to the tip.
    band = max(min(_d2(p) for p in poly), 1.0) * 1.35
    near_set = [p for p in poly if _d2(p) <= band] or [tip]
    root = (
        sum(p[0] for p in near_set) / len(near_set),
        sum(p[1] for p in near_set) / len(near_set),
    )
    ax, ay = tip[0] - root[0], tip[1] - root[1]
    alen = math.hypot(ax, ay) or 1.0
    ux, uy = ax / alen, ay / alen
    px, py = -uy, ux
    # ⚠ Measured from the ROOT, not the wielder — the quad is centred on the
    # SWING. Measuring from a line through the attacker centres it on the
    # attacker, so a swing authored across the chest yields a quad reaching as
    # far below the body as the swing reaches above it, and the art lands half
    # the rise low: the swing looks like it droops whatever the axis says.
    ts = [(p[0] - root[0]) * ux + (p[1] - root[1]) * uy for p in poly]
    offs = [abs((p[0] - root[0]) * px + (p[1] - root[1]) * py) for p in poly]
    return (ux, uy, px, py, min(ts), max(ts) - min(ts), max(offs), root)


def _inside(poly: Sequence[Tuple[float, float]], pt: Tuple[float, float]) -> bool:
    n = len(poly)
    sign = 0
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        cross = (b[0] - a[0]) * (pt[1] - a[1]) - (b[1] - a[1]) * (pt[0] - a[0])
        sign += 1 if cross > 0 else -1
    return abs(sign) == n


def containment(
    poly: Sequence[Tuple[float, float]],
    attacker: Tuple[float, float],
    effect: Image.Image,
    step: int = 2,
) -> Tuple[int, int]:
    """`(inked samples, samples outside the polygon)`.

    Zero outside is the goal and the only number worth reporting to an artist:
    "the player should never feel like they should have hit when they didn't".
    """
    ux, uy, px, py, t_min, length, far_half, root = _swing_quad(poly, attacker)
    alpha = effect.getchannel("A").load()
    w, h = effect.size
    total = outside = 0
    for iy in range(0, h, step):
        for ix in range(0, w, step):
            if alpha[ix, iy] <= 8:
                continue
            total += 1
            t = t_min + (ix / w) * length
            o = ((iy / h) - 0.5) * 2 * far_half
            world = (root[0] + ux * t + px * o, root[1] + uy * t + py * o)
            if not _inside(poly, world):
                outside += 1
    return total, outside


def render_preview(
    character_frame: Image.Image,
    poly: Sequence[Tuple[float, float]],
    attacker: Tuple[float, float],
    effect: Image.Image,
    out: Path,
    pad: int = 70,
) -> Tuple[int, int]:
    """Compose character + polygon + effect, and return the containment counts."""
    ux, uy, px, py, t_min, length, far_half, root = _swing_quad(poly, attacker)

    xs = [p[0] for p in poly] + [attacker[0], 0.0, float(character_frame.width)]
    ys = [p[1] for p in poly] + [attacker[1], 0.0, float(character_frame.height)]
    ox, oy = min(xs) - pad, min(ys) - pad
    canvas = Image.new(
        "RGBA",
        (int(max(xs) - min(xs) + 2 * pad), int(max(ys) - min(ys) + 2 * pad)),
        (16, 18, 26, 255),
    )
    canvas.alpha_composite(character_frame, (int(-ox), int(-oy)))

    # The effect, stretched into the quad and turned onto the swing axis — the
    # same two operations `spawn_one` performs.
    art = effect.resize(
        (max(1, int(length)), max(1, int(2 * far_half))), Image.Resampling.LANCZOS
    )
    art = art.rotate(
        -math.degrees(math.atan2(uy, ux)),
        resample=Image.Resampling.BICUBIC,
        expand=True,
    )
    centre = (
        root[0] + ux * (t_min + length / 2),
        root[1] + uy * (t_min + length / 2),
    )
    canvas.alpha_composite(
        art,
        (int(centre[0] - ox - art.width / 2), int(centre[1] - oy - art.height / 2)),
    )

    d = ImageDraw.Draw(canvas)
    d.polygon([(p[0] - ox, p[1] - oy) for p in poly], outline=POLY_COLOUR)
    for p in poly:
        d.ellipse(
            [p[0] - ox - 2, p[1] - oy - 2, p[0] - ox + 2, p[1] - oy + 2],
            fill=POLY_COLOUR,
        )
    corners = [
        (root[0] + ux * t + px * o, root[1] + uy * t + py * o)
        for t, o in (
            (t_min, -far_half),
            (t_min + length, -far_half),
            (t_min + length, far_half),
            (t_min, far_half),
        )
    ]
    d.polygon([(c[0] - ox, c[1] - oy) for c in corners], outline=QUAD_COLOUR)
    d.ellipse(
        [
            attacker[0] - ox - 4,
            attacker[1] - oy - 4,
            attacker[0] - ox + 4,
            attacker[1] - oy + 4,
        ],
        fill=ATTACKER_COLOUR,
    )
    # A level line through the attacker, because "does this swing point straight
    # ahead" is asked of every jab and cannot be answered by eye without one.
    d.line(
        [(0, attacker[1] - oy), (canvas.width, attacker[1] - oy)],
        fill=(120, 255, 120, 90),
    )

    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out)
    return containment(poly, attacker, effect)


def preview_player_swing(
    animation: str = "attack_side",
    row: str = "side",
    frame: int = 0,
    out: Path | str = "/tmp/swing_preview.png",
) -> Tuple[int, int]:
    """The protagonist's swing, straight out of the generator.

    Imported lazily so this module stays importable without pulling a character
    rig in — the containment helpers above are useful on their own.
    """
    from ..targets.characters import player_robot_v3 as v3
    from ..targets.props import robot_slash

    hitboxes: Dict[str, dict] = v3._translated_legacy_hitboxes()
    entry = hitboxes.get(animation)
    if entry is None or not entry.get("poly"):
        raise SystemExit(
            f"{animation!r} has no authored polygon; known: {sorted(hitboxes)}"
        )
    poly: List[Tuple[float, float]] = [(float(x), float(y)) for x, y in entry["poly"]]

    doc = v3.load_doc()
    attacker = (
        float(doc.frame["center_x"]),
        float(doc.frame["ground_y"]) - (BODY_WORLD_H / FRAME_SCALE) / 2,
    )

    character = v3.render_frame(animation, frame, 3).convert("RGBA")
    effect = robot_slash._draw_frame(row, frame, 5).convert("RGBA")
    return render_preview(character, poly, attacker, effect, Path(out))


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--animation", default="attack_side")
    parser.add_argument("--row", default="side", help="slash sheet row to draw")
    parser.add_argument("--frame", type=int, default=0)
    parser.add_argument("--out", default="/tmp/swing_preview.png")
    args = parser.parse_args(argv)

    total, outside = preview_player_swing(
        args.animation, args.row, args.frame, args.out
    )
    share = outside / max(total, 1) * 100
    print(f"wrote {args.out}")
    print(
        f"  {args.animation} / {args.row} frame {args.frame}: "
        f"{total} inked samples, {outside} outside the polygon ({share:.2f}%)"
    )
    if outside:
        print("  ⚠ part of the drawn effect cannot hit anything.")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
