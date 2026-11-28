"""PF4's in-between oracle: which clips of a part-first target may tween.

A tweened clip draws, between two frames, each part lerped toward its place in
the next frame (`part_flipbook.tween_draws`, the runtime's `tween_into`).
Whether that is right is a question for the target's own rig: drawn at the
fractional frame ``i + 0.5`` (``render(row, i + 0.5, n)``), the rig poses the
true in-between. A clip may tween when, at every frame, the tween is as close
to that in-between as the stepping clip is (it shows frame ``i`` there),
within the replay guard's margin, or replays it within the guard of a
published frame. The last frame is measured
toward the first, as the runtime tweens it, so a clip played once fails there
unless it ends where it began.

A rig that cannot pose a fractional frame (an index into a list of poses)
has no oracle, and its clips keep their defaults.

    python -m ambition_sprite2d_renderer.devtools.tween_oracle <target> <scratch dir>
        prints one JSON line: each clip's verdict
    python -m ambition_sprite2d_renderer.devtools.tween_oracle --summary <dir of those lines>
        prints the `tween_rows` entries of `sprites.yaml`

Measured over every part-first target on 2026-11-19
(`docs/planning/engine/part-first-publication.md`, PF4).
"""

from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

from PIL import Image

#: The in-between measured, as a fraction of the step.
T = 0.5


def oracle(name: str, scratch: Path) -> dict:
    from ambition_sprite2d_renderer.authoring import part_flipbook as pf
    from ambition_sprite2d_renderer.authoring import rigdoc
    from ambition_sprite2d_renderer.registry import discover_all_targets

    out = scratch / name
    shutil.rmtree(out, ignore_errors=True)
    captured: dict = {}
    original = pf.publish_rig_flipbook

    def capture(target, rows, render, outputs, ft, out_dir, tween_rows=None, render_clip=None, track_parents=None):
        if outputs.get("flipbook") is not None and target == name:
            captured.update(render=render, flipbook=outputs["flipbook"], ft=dict(ft))
        return original(target, rows, render, outputs, ft, out_dir, tween_rows, render_clip, track_parents)

    targets = discover_all_targets().targets
    # Each target module imported the function by name: the capture replaces
    # every such reference.
    for module in list(sys.modules.values()):
        if getattr(module, "publish_rig_flipbook", None) is original:
            module.publish_rig_flipbook = capture
    pf.publish_rig_flipbook = capture
    started = time.perf_counter()
    try:
        targets[name].render_sheet(out / "render")
    finally:
        shutil.rmtree(out, ignore_errors=True)
    if not captured:
        return {"target": name, "status": "no part-first flipbook"}
    flipbook, render, ft = captured["flipbook"], captured["render"], captured["ft"]
    flipbook.pack()
    dx, dy = int(ft.get("dx", 0)), int(ft.get("dy", 0))
    # An in-between may sit a pixel from the rig's, as a keyframe may.
    tolerance = dict(pf.CONTINUOUS_REPLAY_TOLERANCE, radius=1)

    def place(frame: Image.Image) -> Image.Image:
        canvas = Image.new("RGBA", flipbook.frame_size, (0, 0, 0, 0))
        rigdoc.composite_canvas(canvas, frame, (dx, dy))
        return canvas

    def measure(truth, draws, row, index):
        canvas = Image.new("RGBA", flipbook.frame_size, (0, 0, 0, 0))
        flipbook.draw_frame(canvas, row, index, flipbook.feet, draws=draws)
        wrong, blob = pf.replay_measure(truth, canvas, **tolerance)
        return wrong, blob, wrong <= pf.CONTINUOUS_REPLAY_PARITY and blob <= pf.CONTINUOUS_REPLAY_BLOB

    clips = {}
    for row, (_duration, frames) in flipbook.clips.items():
        n = len(frames)
        if n < 2:
            continue
        saved = flipbook.tweens.get(row)
        flipbook.tweens[row] = pf.TWEEN_LINEAR
        verdict = {"tweened": saved == pf.TWEEN_LINEAR, "holds": True, "fails_at": None}
        for i in range(n):
            try:
                truth = place(render(row, i + T, n))
            except Exception as refused:  # noqa: BLE001 - a rig that cannot pose it has no oracle
                verdict.update(holds=False, fails_at=f"{i}: no in-between pose ({type(refused).__name__})")
                break
            try:
                wrong, blob, replays = measure(truth, pf.tween_draws(flipbook, row, i, T), row, i)
            except ZeroDivisionError:
                verdict.update(holds=False, fails_at=f"{i}: a part tweens through zero scale (a mirror)")
                break
            held, held_blob, _ = measure(truth, frames[i], row, i)
            # No worse than holding, within the guard's own margin of one
            # picture (`CONTINUOUS_REPLAY_PARITY`, `CONTINUOUS_REPLAY_BLOB`).
            no_worse = wrong <= held + pf.CONTINUOUS_REPLAY_PARITY and blob <= held_blob + pf.CONTINUOUS_REPLAY_BLOB
            if not (replays or no_worse):
                verdict.update(holds=False, fails_at=f"{i}: {wrong:.2%} wrong, blob {blob} (held: {held:.2%}, blob {held_blob})")
                break
        if saved is None:
            flipbook.tweens.pop(row, None)
        else:
            flipbook.tweens[row] = saved
        clips[row] = verdict
    return {"target": name, "status": "ok", "seconds": round(time.perf_counter() - started, 1), "clips": clips}


def summary(directory: Path) -> str:
    """The `tween_rows` entries: each measured target's clips that hold, in
    its order, for a target whose verdict differs from the default."""
    from ambition_sprite2d_renderer.authoring.part_flipbook import LOCOMOTION_LOOPS

    lines = []
    for path in sorted(directory.glob("*.json")):
        found = [line for line in path.read_text().splitlines() if line.startswith('{"target"')]
        if not found:
            continue
        result = json.loads(found[-1])
        if result.get("status") != "ok":
            continue
        clips = result["clips"]
        holds = [row for row, v in clips.items() if v["holds"]]
        # A clip with no in-between pose keeps the default: unmeasured is not wrong.
        unmeasured = [row for row, v in clips.items() if "no in-between pose" in (v.get("fails_at", v.get("fail_at")) or "")]
        default = [row for row in clips if row in LOCOMOTION_LOOPS]
        chosen = [row for row in clips if row in holds or (row in default and row in unmeasured)]
        if chosen != default:
            lines.append(f"  {result['target']}: [{', '.join(chosen)}]")
    return "\n".join(lines)


def main(argv) -> int:
    if argv[:1] == ["--summary"]:
        print(summary(Path(argv[1])))
        return 0
    print(json.dumps(oracle(argv[0], Path(argv[1]))), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
