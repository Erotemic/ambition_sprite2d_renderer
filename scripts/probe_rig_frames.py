"""Measure a code-drawn character module frame by frame, before publishing it.

    python scripts/probe_rig_frames.py characters.ramen_nujan OUT_DIR [--replay]

The module exposes ``ROWS``, ``FRAME_SIZE``, ``_render_frame(row, index, count)``
and ``render(out_dir)``.

Always: every frame whose art comes within 2 pixels of the frame's edge (art
past the edge is cut off in the sheet).

``--replay``: renders the target into ``OUT_DIR/gen`` and lists every frame the
part flipbook's final replay does not reproduce (a wrong blob over
``CONTINUOUS_REPLAY_BLOB``, or parity over ``CONTINUOUS_REPLAY_PARITY``),
instead of stopping at the first as a publish does. ``OUT_DIR/bad.png`` shows
the five worst: the render, the replay, and the wrong pixels, four times size.
"""

from __future__ import annotations

import argparse
import importlib
from pathlib import Path

import numpy as np
from PIL import Image

from ambition_sprite2d_renderer.authoring import part_flipbook as pf


def frames_near_the_edge(module, margin: int = 2) -> dict:
    fw, fh = module.FRAME_SIZE
    near = {}
    for name, count, _ms in module.ROWS:
        for index in range(count):
            box = module._render_frame(name, index, count).getchannel("A").getbbox()
            if box is None:
                continue
            room = min(box[0], box[1], fw - box[2], fh - box[3])
            if room < margin:
                near[(name, index)] = (box, room)
    return near


def largest_blob(wrong) -> list:
    todo = {(int(y), int(x)) for y, x in zip(*np.where(wrong))}
    best: list = []
    while todo:
        stack, blob = [todo.pop()], []
        while stack:
            y, x = stack.pop()
            blob.append((y, x))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    q = (y + dy, x + dx)
                    if q in todo:
                        todo.discard(q)
                        stack.append(q)
        if len(blob) > len(best):
            best = blob
    return best


def replay_failures(module, out: Path) -> list:
    """Every frame of the FINAL flipbook against its render. The sharing steps
    before it run with the real measures (a spy that forgave them would let
    them share parts that do not replay)."""
    final: list = []
    seen: list = []
    blob_of, parity_of, split = pf.largest_wrong_blob, pf.parity, pf._split_symmetric_parts

    def after_split(*args, **kw):
        result = split(*args, **kw)
        final.append(True)
        return result

    def spy_blob(frame, replayed, **kw):
        blob = blob_of(frame, replayed, **kw)
        if not final:
            return blob
        wrong, _drawn = pf.wrong_pixels(frame, replayed, kw["threshold"], kw["radius"], kw["edge"])
        seen.append((blob, parity_of(frame, replayed, **kw), frame, replayed, np.asarray(wrong)))
        return 0

    pf._split_symmetric_parts = after_split
    pf.largest_wrong_blob = spy_blob
    pf.parity = lambda *args, **kw: 0.0 if final else parity_of(*args, **kw)
    try:
        module.render(out / "gen")
    finally:
        pf._split_symmetric_parts, pf.largest_wrong_blob, pf.parity = split, blob_of, parity_of
    keys = [(name, index) for name, count, _ms in module.ROWS for index in range(count)]
    assert len(seen) == len(keys), (len(seen), len(keys))
    bad = sorted(
        ((s[0], round(s[1], 4), key) for s, key in zip(seen, keys) if s[0] > pf.CONTINUOUS_REPLAY_BLOB or s[1] > pf.CONTINUOUS_REPLAY_PARITY),
        reverse=True,
    )
    crops = []
    for blob, _parity, key in bad[:5]:
        _b, _p, frame, replayed, wrong = seen[keys.index(key)]
        cells = largest_blob(wrong)
        cx, cy = int(np.mean([c[1] for c in cells])), int(np.mean([c[0] for c in cells]))
        print(f"  {key}: a blob of {blob} about {(cx, cy)}")
        box = (cx - 24, cy - 24, cx + 24, cy + 24)
        strip = Image.new("RGBA", (48 * 3, 48), (60, 60, 80, 255))
        for k, image in enumerate((frame, replayed, Image.fromarray((wrong * 255).astype("uint8")))):
            strip.alpha_composite(image.convert("RGBA").crop(box), (k * 48, 0))
        crops.append(strip.resize((strip.width * 4, strip.height * 4), Image.Resampling.NEAREST))
    if crops:
        sheet = Image.new("RGBA", (crops[0].width, sum(c.height for c in crops)))
        for k, crop in enumerate(crops):
            sheet.paste(crop, (0, k * crop.height))
        sheet.save(out / "bad.png")
    return bad


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("module", help="under ambition_sprite2d_renderer.targets, e.g. characters.ramen_nujan")
    parser.add_argument("out", type=Path)
    parser.add_argument("--replay", action="store_true")
    args = parser.parse_args(argv)
    module = importlib.import_module(f"ambition_sprite2d_renderer.targets.{args.module}")
    args.out.mkdir(parents=True, exist_ok=True)
    near = frames_near_the_edge(module)
    print(f"frames within 2 px of an edge: {near or 'none'}")
    if args.replay:
        bad = replay_failures(module, args.out)
        print(f"{len(bad)} frame(s) the flipbook does not replay: {bad[:30]}")
        return 1 if bad or near else 0
    return 1 if near else 0


if __name__ == "__main__":
    raise SystemExit(main())
