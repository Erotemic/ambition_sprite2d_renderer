"""Every variation of every lineage, and which of them are holistic looks.

The survey draws a still at each candidate commit of a lineage; each run of
identical pixels is one VARIATION (`survey.eras`). Most variations are small:
a burst of commits on one day that patch a detail. A HOLISTIC look is what a
burst ends on, unless it looks almost the same as the holistic look before it
(a later refactor that redraws the same look keeps the look's first author).
A burst can hold more than one look: a variation that the next one redraws
completely (Alice's white coat, replaced ten minutes later) ends a look too.

    burst     consecutive variations less than `BURST_HOURS` apart
    look end  the last variation of a burst, or one whose next variation
              differs from it by at least `NEW_LOOK`
    holistic  a look end whose still differs from the previous holistic look
              by at least `SAME_LOOK`

A difference is the mean difference of two stills, cropped to the character
and scaled to one size (0 = equal, 1 = opposite). Measured on Alice's 12
variations: a patch differs by 0.002 to 0.011, a new look by 0.054 to 0.116.

A lineage is surveyed in TRACKS: its `ids` (one target under its old names)
is one track, and each other target it names (a generation, a form) is its
own track, because two generations are drawn at the same commits.

The record (`variations.yaml`, beside `lineages.yaml`) keeps every variation
with its distance, so a change of the thresholds needs no new render. It is
derived: `python -m design_history survey --all --jobs N` rewrites it. The
stills stay in the design-history cache.
"""

from __future__ import annotations

import concurrent.futures
import dataclasses
import datetime
from pathlib import Path

import yaml

from .stills import Worktrees, still_for

#: Two variations closer in time than this are one burst of work.
BURST_HOURS = 8.0
#: Two stills closer than this are one look.
SAME_LOOK = 0.035
#: A next variation this far from a variation replaces its look, in a burst too.
NEW_LOOK = 0.04
#: The side of the square that two stills are compared at.
_SIDE = 48

RECORD = Path(__file__).resolve().parent / "variations.yaml"


def distance(a: Path, b: Path) -> float:
    """The mean difference of two stills, each cropped to the character, fit
    into one square and laid on white: 0 for equal looks, up to 1."""
    from PIL import Image

    from .progression import character_bbox

    def norm(path: Path):
        with Image.open(path) as image:
            image = image.convert("RGBA")
            image = image.crop(character_bbox(image) or (0, 0, *image.size))
            image.thumbnail((_SIDE, _SIDE), Image.LANCZOS)
            square = Image.new("RGBA", (_SIDE, _SIDE), (255, 255, 255, 255))
            square.alpha_composite(image, ((_SIDE - image.width) // 2, _SIDE - image.height))
            return square.convert("RGB").tobytes()

    pa, pb = norm(a), norm(b)
    return sum(abs(x - y) for x, y in zip(pa, pb)) / (255 * len(pa))


@dataclasses.dataclass
class Variation:
    commit: str
    date: str
    segment: str
    target: str
    pixels: str
    still: Path
    by: str = ""
    subject: str = ""
    burst_end: bool = False
    #: Difference from the variation before it (None for the first).
    step: float | None = None
    look_end: bool = False
    #: Distance from the previous holistic look (None for the first).
    change: float | None = None
    holistic: bool = False


def classify(found: list[Variation], *, burst_hours: float = BURST_HOURS, same_look: float = SAME_LOOK,
             new_look: float = NEW_LOOK) -> None:
    """Mark the burst ends, the look ends and the holistic looks of `found`
    (oldest first)."""
    when = [datetime.datetime.fromisoformat(v.date) for v in found]
    for i, v in enumerate(found):
        v.step = None if i == 0 else round(distance(found[i - 1].still, v.still), 4)
    previous = None
    for i, v in enumerate(found):
        v.burst_end = i == len(found) - 1 or (when[i + 1] - when[i]).total_seconds() >= burst_hours * 3600
        v.look_end = v.burst_end or found[i + 1].step >= new_look
        if not v.look_end:
            continue
        v.change = None if previous is None else round(distance(previous.still, v.still), 4)
        if previous is None or v.change >= same_look:
            v.holistic = True
            previous = v


def render_all(tasks: list[tuple], *, python: str, store: Path, cache: Path, jobs: int, log=print) -> None:
    """Draw every `(segment, sha, ids, pick)` still not yet in the cache, on
    `jobs` processes. Each process has its own worktrees."""
    from .stills import cached_still

    todo = [t for t in tasks if cached_still(cache, t[1], list(t[2]), t[3]) is None
            and not (cache / "stills" / f"{_key(t)}.failed").exists()]
    log(f"{len(tasks)} stills, {len(tasks) - len(todo)} cached, {len(todo)} to draw on {jobs} process(es)")
    if not todo:
        return
    todo.sort(key=lambda t: (t[0].name, t[1]))
    chunks = [todo[i::jobs] for i in range(jobs)]
    with concurrent.futures.ProcessPoolExecutor(max_workers=jobs) as pool:
        futures = [pool.submit(_draw_chunk, chunk, python, str(store), str(cache), f"w{i}") for i, chunk in enumerate(chunks) if chunk]
        done = 0
        for fut in concurrent.futures.as_completed(futures):
            done += fut.result()
            log(f"  a worker finished: {done}/{len(todo)} drawn")


def _key(task) -> str:
    from .stills import still_key

    return still_key(task[1], list(task[2]), task[3])


def _draw_chunk(chunk, python: str, store: str, cache: str, slot: str) -> int:
    trees = Worktrees(Path(store), Path(cache), slot=slot)
    try:
        for n, (seg, sha, ids, pick) in enumerate(chunk, 1):
            still = still_for(python=python, worktrees=trees, cache=Path(cache), seg=seg, sha=sha, target_ids=list(ids), pick=pick)
            print(f"  [{slot} {n}/{len(chunk)}] {sha[:9]} {'+'.join(ids)} {still.pixel_hash or 'FAILED'}", flush=True)
    finally:
        trees.remove()
    return len(chunk)


def write(record: dict[str, dict], path: Path = RECORD) -> None:
    header = (
        "# Every variation of each lineage that the survey drew, and which are\n"
        "# holistic looks (design_history/variations.py). DERIVED: rewritten by\n"
        "# `python -m design_history survey --all`; do not edit by hand. The\n"
        "# curated looks are the `eras` of lineages.yaml.\n"
    )
    text = yaml.safe_dump({"lineages": record}, sort_keys=True, allow_unicode=True, width=120)
    partial = path.with_suffix(".yaml.partial")
    partial.write_text(header + text, encoding="utf-8")
    partial.replace(path)


def load(path: Path = RECORD) -> dict[str, dict]:
    if not path.is_file():
        return {}
    return (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("lineages") or {}


def tracks(name: str, spec: dict) -> list[list[str]]:
    """The id lists a lineage is surveyed with: its `ids`, then each other
    target it names, alone."""
    from .characters import lineage_targets

    ids = [str(i) for i in spec.get("ids") or []] or [name]
    return [ids, *([t] for t in lineage_targets(spec) if t not in ids)]


def as_rows(found: list[Variation]) -> list[dict]:
    return [
        {
            "commit": v.commit[:12], "date": v.date, "segment": v.segment, "target": v.target,
            "pixels": v.pixels, "by": v.by, "subject": v.subject[:90],
            "burst_end": v.burst_end, "step": v.step, "look_end": v.look_end, "change": v.change, "holistic": v.holistic,
        }
        for v in found
    ]
