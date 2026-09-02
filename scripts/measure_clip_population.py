#!/usr/bin/env python3
"""Measure the clip guard's population, per target, and split it by SHAPE.

D129's open half. The 2026-08-31 sweep established that the guard's report is a
POPULATION, not a defect list: some of the frames it names are severed art, and
some are art drawn deliberately flush to a fitted frame. The two are
indistinguishable to the guard, whose whole criterion is "the shape arrives at
the boundary without tapering" — and a flat pixel-art foot standing on the floor
does not taper either. Acting on the raw list means inflating canvases to silence
true negatives, which MOVES the ground contact of every sprite so treated.

⛔ THIS SCRIPT EDITS NO ART AND CHANGES NO GUARD. It renders, records, and
prints. The split it reports is evidence for deciding which frames are worth an
authoring fix; it is not itself a fix, and a frame it calls FLAT is not thereby
declared correct — only "not distinguishable from deliberate by silhouette".

WHAT IT MEASURES, per flagged edge, is the guard's own inward profile: the count
of opaque pixels on the boundary line and on each of the six lines inside it, plus
the two numbers the guard reduces that profile to and then throws away.

⛔⛔ AND THE OBVIOUS CLASSIFIER DOES NOT SURVIVE THE DATA, which is the finding
this script exists to record. The first draft split the population into "seated
flush on purpose" and "still moving when it was cut", on the theory that a
severed shape is changing as it reaches the boundary and a seated one has
arrived. Measured, `pirate_admiral`'s plume — a TIP, established 2026-08-31 — and
`super_sanic`'s historical spike CUT have the same signature:

    pirate_admiral top  7  9  9 10 10 11 14   ratio 0.50  <- a tip
    super_sanic    idle 12 14 17 18 20 22 25  ratio 0.50  <- a cut
    mary_o         idle 24 24 24 24 24 24 24  ratio 1.00  <- a flat sole

Both are steadily narrowing toward the boundary and both land exactly on the
guard's 0.5 threshold. THE SILHOUETTE CANNOT SEPARATE THEM, and it never could:
the drawing canvas IS the logical frame, so the ink beyond it was never rendered
and there is nothing left to look at. A classifier that answered anyway would be
inventing a distinction, which on this row means inflating canvases and moving
sprites' ground contact on the strength of it.

The third line is the class that CAN be decided, and is: a composited frame knows
whether its sprite landed whole, and says so — that marker retires the flat-sole
false positives (41 frames of the playable protagonist) without a heuristic.

SO THIS RANKS RATHER THAN CLASSIFIES. For each flagged edge it reports how much
ink arrives at the boundary (as a fraction of the edge's length — the stake) and
how squarely it arrives (the guard's ratio — the confidence), ordered so the
frames where a cut would cost the most come first. That is a worklist an author
can spend a day on. It is not a defect list, and no row of it is evidence that a
frame is wrong.

USAGE
    python scripts/measure_clip_population.py [--kind module] [--json OUT.json]
    python scripts/measure_clip_population.py --target mary_o --target sanic
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ambition_sprite2d_renderer.authoring import sheet_build  # noqa: E402
from ambition_sprite2d_renderer.registry.discovery import (  # noqa: E402
    discover_all_targets,
)

#: A profile whose spread across the whole depth is under this fraction of its
#: boundary count is FLAT — it arrives at the boundary at the width it already
#: had. Set from `mary_o`'s sole (24 24 24 ... , spread 0) with room for a pixel
#: of antialiasing, not tuned to make any target land anywhere.
_FLAT_SPREAD = 0.06
#: Below this, a profile is TAPERING: it is measurably narrower at the boundary
#: than just inside it. `pirate_admiral` is 0.50 and `super_sanic`'s cut was
#: 0.50, so this describes the SHAPE and settles nothing about the cause.
_TAPER_RATIO = 0.85


class InstrumentError(Exception):
    """The recorder itself failed.

    ⛔ Kept distinct from a render failure and re-raised rather than tabulated.
    The first run of this script tabulated its own `NameError` as "pirate_admiral
    would not render", which is a measurement tool reporting a defect in the
    thing it is measuring when the defect is in itself.
    """


def edge_profile(frame, edge: str, depth: int) -> List[int]:
    """Opaque counts on the boundary line and each line inward, for one edge.

    The guard's own strips, by the guard's own constants — it keeps only the
    boundary count and the inward maximum, and this keeps the sequence.
    """
    alpha = frame.getchannel("A")
    width, height = frame.size
    boxes = {
        "top": lambda d: (0, d, width, d + 1),
        "bottom": lambda d: (0, height - 1 - d, width, height - d),
        "left": lambda d: (d, 0, d + 1, height),
        "right": lambda d: (width - 1 - d, 0, width - d, height),
    }
    line_box = boxes[edge]
    counts = []
    for d in range(depth + 1):
        histogram = alpha.crop(line_box(d)).histogram()
        counts.append(sum(histogram[sheet_build._CLIP_OPAQUE + 1 :]))
    return counts


def edge_span(edge: str, size: Tuple[int, int]) -> int:
    """How long the flagged edge is — the denominator for "how much is at stake"."""
    width, height = size
    return width if edge in ("top", "bottom") else height


def describe(profile: List[int], edge: str, size: Tuple[int, int]) -> dict:
    """The numbers the guard computes, kept instead of reduced to a boolean.

    ⚠ `shape` is a DESCRIPTION, not a verdict. TAPERING covers both a tip and a
    spike cut off mid-narrowing; FLAT covers both a sole on the floor and a cut
    straight through a wide flat region. See the module docstring — separating
    those needs the ink that was never rendered.
    """
    at_edge = profile[0]
    inward = max(profile[1:], default=0)
    ratio = at_edge / inward if inward else float("inf")
    spread = (max(profile) - min(profile)) / at_edge if at_edge else 0.0
    if spread <= _FLAT_SPREAD:
        shape = "FLAT"
    elif ratio < _TAPER_RATIO:
        shape = "TAPERING"
    else:
        shape = "ABRUPT"
    span = edge_span(edge, size)
    stake = at_edge / span if span else 0.0
    return {
        "at_edge": at_edge,
        "inward_max": inward,
        "ratio": round(ratio, 3) if inward else None,
        "stake": round(stake, 4),
        "shape": shape,
        # ⭐ THE ORDERING KEY, and it is deliberately a product: a wide edge run
        # that arrives squarely is where a cut costs the most art, and a narrow
        # one that tapers is where it costs the least. Neither factor alone
        # ranks the list usefully — `pirate_admiral` is high-confidence and
        # trivial (7px of plume), which is exactly the frame an author should
        # reach last.
        "severity": round(stake * min(ratio, 1.0), 4) if inward else round(stake, 4),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=["module", "config", "all"], default="all")
    parser.add_argument("--target", action="append", default=[])
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()

    report = discover_all_targets()
    targets = [t for _, t in sorted(report.targets.items())]
    if args.kind != "all":
        targets = [t for t in targets if t.kind == args.kind]
    if args.target:
        wanted = set(args.target)
        targets = [t for t in targets if t.name in wanted]

    # ⭐ WRAP THE GUARD, DO NOT REIMPLEMENT IT. The 2026-08-31 sweep's first pass
    # measured 42 of 209 by reimplementing the render loop over `module.ROWS`,
    # which 116 targets do not export — a sample reported as a population. The
    # guard is called from exactly one place on the real road, with the frame in
    # hand, before padding; wrapping it there is the only way to see every frame
    # every target actually produces.
    original = sheet_build.clipped_frame_edges
    captured: List[Tuple[str, List[int], Tuple[int, int]]] = []

    def recording_guard(frame):
        edges = original(frame)
        if not edges:
            return edges
        try:
            depth = min(
                sheet_build._CLIP_DEPTH, frame.width // 2, frame.height // 2
            )
            for edge in edges:
                captured.append(
                    (edge, edge_profile(frame, edge, depth), frame.size)
                )
        except Exception as error:  # noqa: BLE001
            raise InstrumentError(f"recorder failed on a {frame.size} frame: {error}")
        return edges

    sheet_build.clipped_frame_edges = recording_guard

    results: Dict[str, dict] = {}
    failures: Dict[str, str] = {}
    started = time.time()
    try:
        for index, target in enumerate(targets, start=1):
            captured.clear()
            print(
                f"[{index}/{len(targets)}] {target.name} ({target.kind})",
                file=sys.stderr,
                flush=True,
            )
            # ⛔ RETRY ONCE, because the first full sweep lost a target to
            # `OSError: Too many open files` — machine-wide pressure from another
            # build running beside it, not anything about the target, which
            # rendered fine on its own seconds later. A census that reports a
            # transient as a property of the art is worse than no census.
            error = None
            for attempt in (1, 2):
                captured.clear()
                try:
                    with tempfile.TemporaryDirectory() as out_dir:
                        target.render_sheet(Path(out_dir))
                    error = None
                    break
                except InstrumentError:
                    raise
                except Exception as caught:  # noqa: BLE001
                    error = caught
                    if attempt == 1:
                        print(
                            f"    retrying after {type(caught).__name__}",
                            file=sys.stderr,
                            flush=True,
                        )
            if error is not None:
                # ⛔ A TARGET THAT WILL NOT RENDER IS NOT A CLEAN TARGET. Counting
                # it as zero flagged frames is how a census reports an
                # improvement it did not measure.
                failures[target.name] = f"{type(error).__name__}: {error}"
                continue
            if not captured:
                continue
            rows = [
                {"edge": edge, "profile": profile, "size": list(size),
                 **describe(profile, edge, size)}
                for edge, profile, size in captured
            ]
            rows.sort(key=lambda r: -r["severity"])
            results[target.name] = {
                "kind": target.kind,
                "category": target.category,
                "flagged_edges": len(rows),
                "worst_severity": rows[0]["severity"],
                "worst_stake": rows[0]["stake"],
                "shapes": {
                    s: sum(1 for r in rows if r["shape"] == s)
                    for s in ("FLAT", "TAPERING", "ABRUPT")
                },
                "rows": rows,
            }
    finally:
        sheet_build.clipped_frame_edges = original

    elapsed = time.time() - started
    total_edges = sum(r["flagged_edges"] for r in results.values())
    print()
    print(
        f"rendered {len(targets)} target(s) in {elapsed:.0f}s — "
        f"{len(results)} flagged ({total_edges} edge(s)), "
        f"{len(failures)} would not render"
    )
    print()
    print(
        f"{'target':34} {'edges':>5} {'worst':>6} {'stake':>6} "
        f"{'FLAT':>5} {'TAPER':>5} {'ABRUPT':>6}  worst edge profile"
    )
    for name, row in sorted(
        results.items(), key=lambda kv: (-kv[1]["worst_severity"], kv[0])
    ):
        worst = row["rows"][0]
        print(
            f"{name:34} {row['flagged_edges']:5} {row['worst_severity']:6.3f} "
            f"{worst['stake']:6.3f} {row['shapes']['FLAT']:5} "
            f"{row['shapes']['TAPERING']:5} {row['shapes']['ABRUPT']:6}  "
            f"{worst['edge']:6} {worst['profile']}"
        )
    if failures:
        # ⛔ NOT A FOOTNOTE. A target that would not render was not measured, and
        # a census that reports the rest as "the population" is the sample error
        # this row already made once.
        print()
        # ⛔ SPLIT BY REASON. A missing native dependency is a property of THIS
        # MACHINE and the same targets will render elsewhere; anything else is a
        # property of the target and belongs in front of whoever owns it.
        missing_dep = {
            n: e for n, e in failures.items() if "resvg-py" in e
        }
        other = {n: e for n, e in failures.items() if n not in missing_dep}
        print(
            f"NOT MEASURED — {len(failures)} target(s), and NOT counted as clean:"
        )
        if missing_dep:
            print(
                f"  {len(missing_dep)} need native resvg-py, absent on this "
                f"machine — re-run these where it is installed:"
            )
            print(f"    {', '.join(sorted(missing_dep))}")
        for name, error in sorted(other.items()):
            print(f"  {name}: {error}")
    print()
    print(
        "severity = stake x min(ratio,1): how much ink arrives at the boundary, "
        "times how squarely."
    )
    print(
        "⚠ This is a WORKLIST ORDER, not a defect list. Shape describes the "
        "silhouette and settles nothing"
    )
    print(
        "  about cause — a tip and a spike cut mid-narrowing are both TAPERING. "
        "See the module docstring."
    )

    if args.json:
        args.json.write_text(
            json.dumps(
                {
                    "elapsed_seconds": round(elapsed, 1),
                    "targets_rendered": len(targets),
                    "results": results,
                    "failures": failures,
                },
                indent=2,
            )
        )
        print(f"wrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
