"""A noodling: the Flying Spaghetti Monster's lesser appendage, sent after you.

The god's own vocabulary at a fraction of its size — a small bell of noodles,
ONE meatball on top, two eye stalks, and a few short noodles trailing under it —
so the minion reads as the god's without being mistaken for it. It swims at you
in the same beats and bites on contact.

It borrows the god's drawing primitives (`flying_spaghetti_monster_boss`) and
draws in the god's geometry frame, scaled about its own centre; the sheet
builder crops the frame to the small body.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

from PIL import Image

from ...authoring import rigdoc
from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw
from . import flying_spaghetti_monster_boss as god

TARGET_NAME = "fsm_noodling"
# The god's work frame; the builder crops to the body.
FRAME_SIZE = god.FRAME_SIZE
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 6, 120),
    ("drift", 6, 100),
    ("attack", 5, 80),
    ("hurt", 3, 90),
    ("death", 6, 110),
]
LOOPING = {"idle", "drift"}
# Its size relative to the god.
SCALE = 0.36
CENTRE = god.BELL_CENTRE
BELL_RX, BELL_TOP, BELL_SKIRT = 70.0, 44.0, 22.0
# (rim degrees, length, phase, tip curl)
NOODLES = [(150, 90, 0.0, -10), (118, 110, 1.3, 9), (90, 118, 2.4, -9), (62, 110, 0.7, 10), (30, 90, 1.9, -9)]

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_fsm_noodling",
        "display_name": "Noodling",
    },
    "body": {
        "body_plan": "Blob",
        "body_kind": "Small",
        "mass_class": "Light",
        "locomotion_hint": "Float",
        "traits": ["floating", "noodle", "minion"],
    },
    "brain": {"default_preset": "aerial"},
    "tags": ["enemy", "floating", "minion"],
    "authoring_description": (
        "A lesser appendage of the Flying Spaghetti Monster: a palm-sized bell of "
        "noodles with one meatball and two stalk eyes, sent swimming after whoever "
        "angered its god."
    ),
}


def _pose(anim: str, i: int, n: int):
    loop = anim in LOOPING
    t = i / float(n) if loop else i / float(max(1, n - 1))
    cyc = math.tau * t
    beat = max(0.0, math.sin(cyc)) ** 2
    p = dict(bob=0.0, tilt=0.0, squash=0.0, trail=0.0, flare=0.0, limp=0.0, lunge=0.0, eyes="open", aim=20.0, hurt=0.0)
    if anim == "idle":
        p.update(bob=-8 * beat + 4, squash=0.08 * beat, flare=0.4 * beat, aim=20 + 30 * math.sin(cyc))
    elif anim == "drift":
        p.update(bob=-6 * beat, tilt=8, trail=32 + 6 * math.cos(cyc), squash=0.06 * beat, aim=0)
    elif anim == "attack":
        lunge = math.sin(math.pi * t)
        p.update(lunge=lunge, tilt=14 * lunge, squash=-0.1 * lunge, trail=30 * lunge, eyes="angry", aim=10)
    elif anim == "hurt":
        h = math.sin(math.pi * min(1.0, (i + 1) / n))
        p.update(hurt=h, squash=0.14 * h, tilt=-10 * h, flare=0.8 * h, eyes="squeeze")
    elif anim == "death":
        c = 0.5 - 0.5 * math.cos(math.pi * t)
        p.update(bob=30 * c, tilt=30 * c, limp=c, squash=0.14 * c, eyes="dead" if c > 0.3 else "squeeze", aim=90)
    p["time"] = cyc
    return p


def _render_frame(anim: str, i: int, n: int) -> Image.Image:
    p = _pose(anim, i, n)
    size = (god._s(god.WORK_FRAME_SIZE[0]), god._s(god.WORK_FRAME_SIZE[1]))
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = blending_draw(img)
    sx, sy = 1.0 + p["squash"], 1.0 - p["squash"]
    cx, cy = CENTRE[0] + 30 * p["lunge"], CENTRE[1] + p["bob"]

    def P(x: float, y: float) -> god.Point:
        rx, ry = god._rot(x * sx * SCALE, y * sy * SCALE, p["tilt"])
        return (cx + rx, cy + ry)

    w = 10.0 * SCALE * 2.2  # noodle width, thicker than a straight scale so it reads small
    # Trailing noodles, forward kinematics like the god's.
    for k, (rim, length, phase, curl) in enumerate(NOODLES):
        base = P(math.cos(math.radians(rim)) * BELL_RX * 0.8, math.sin(math.radians(rim)) * BELL_SKIRT * 0.9)
        heading = 90.0 - (90.0 - rim) * (0.8 + 0.8 * p["flare"]) + p["trail"] + p["tilt"]
        if p["limp"] > 0:
            heading = god._lerp(heading, 90.0 - (90.0 - rim) * 1.6, p["limp"])
        segs = 10
        seg = length * SCALE / segs
        turns, angle = [], heading
        for j in range(segs):
            s = j / (segs - 1)
            wv = 11.0 * (0.45 + 0.55 * s) * math.sin(0.7 * j - p["time"] - phase) * (1 - p["limp"])
            tip = curl * max(0.0, (s - 0.6) / 0.4) * (1 - p["limp"])
            droop = (90.0 - angle) * (0.05 + 0.14 * s) + 8.0 * math.sin(j * 1.3 + phase * 3.0) * (1 - 0.5 * s)
            turn = god._lerp(wv + tip + p["trail"] * 0.05 * s, droop, p["limp"])
            turns.append(turn)
            angle += turn
        god._draw_noodle(draw, god._smooth(god._chain(base, heading, seg, turns)), w, god.NOODLE if k % 2 else god.NOODLE_BACK, highlight=k % 2 == 1)
    # The bell: a small heap of looping strands.
    for k in range(14):
        a0 = god._hash(k, 31) * math.tau
        sweep = 2.4 + 1.6 * god._hash(k, 32)
        r0 = 0.4 + 0.45 * god._hash(k, 33)
        pts = []
        for m in range(21):
            a = a0 + sweep * m / 20
            r = min(1.0, max(0.15, r0 + 0.2 * math.sin(2.3 * a + p["time"] * 0.5 + k)))
            ry = BELL_TOP if math.sin(a) < 0 else BELL_SKIRT
            pts.append(P(math.cos(a) * BELL_RX * r, math.sin(a) * ry * r - 6))
        god._draw_noodle(draw, pts, w, god.NOODLE_BACK if k < 5 else god.NOODLE, highlight=k >= 5)
    # Eye stalks, then the one meatball in front of them.
    eyes = []
    for side in (-1.0, 1.0):
        a = P(side * 10, -20)
        b = P(side * 34, -52)
        c = P(side * 26 + 4 * math.sin(p["time"] + side), -80 + 20 * p["limp"])
        if p["limp"] > 0:
            c = (c[0] + side * 16 * p["limp"], c[1] + 20 * p["limp"])
        god._draw_noodle(draw, god._smooth([a, b, c]), w * 0.9, god.NOODLE)
        eyes.append(c)
    god._draw_meatball(draw, P(0, -18), 30.0 * SCALE * 1.4, 0.04 + p["squash"] * 0.5, 17)
    for k, c in enumerate(eyes):
        god._draw_eye(draw, c, 16.0 * SCALE * 1.5, p["aim"], p["eyes"], -1.0 if k == 0 else 1.0)
    if anim == "hurt" and i == 0:
        flash = Image.new("RGBA", img.size, (255, 255, 255, 0))
        flash.putalpha(img.getchannel("A").point(lambda v: v * 150 // 255))
        # Through rigdoc's seams: the body's shapes, then the flash as one picture.
        flashed = Image.new("RGBA", img.size, (0, 0, 0, 0))
        rigdoc.composite_canvas(flashed, img)
        rigdoc.composite_canvas(flashed, flash)
        img = flashed
    return god._downsample(img)


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=_render_frame,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        auto_crop=True,
        crop_margin=6,
        actor_metadata=ACTOR_METADATA,
    )
    parts = publish_rig_flipbook(TARGET_NAME, ROWS, _render_frame, outputs, frame_transform, Path(out_dir))
    return [outputs[k] for k in ("spritesheet", "yaml", "ron", "actor", "preview", "canonical", "canonical_transparent")] + list(parts.values())


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Render the FSM's noodling minion.")
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parents[2] / "generated" / TARGET_NAME)
    args = parser.parse_args(argv)
    for path in render(args.out_dir):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
