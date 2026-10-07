"""Find the commits where a character may have changed, and see which did.

A lineage names the file patterns that draw it. Every commit that touches a
matching file is a CANDIDATE; the still made at each is compared by pixels, and
the first commit of each new look is a design era. Candidates are cheap to
find and slow to draw, so stills are cached and a sweep can be resumed.

A look that changed through a SHARED helper (a rig used by many characters) is
invisible to path matching. Name that helper in the lineage's ``paths``, or ask
for ``--sweep N``: every N-th commit of the lineage's life is drawn as well.
"""

from __future__ import annotations

import dataclasses
import re
from pathlib import Path

from .store import SEGMENTS, Commit, Segment, git, touching
from .stills import Still, Worktrees, still_for


@dataclasses.dataclass
class Candidate:
    commit: Commit
    segment: Segment
    paths: list[str]
    still: Still | None = None


def history(store: Path) -> list[tuple[Commit, Segment, list[str]]]:
    """Every renderer-touching commit of every segment, oldest first.

    The first segment holds renderer content only until the repository was
    split; its later commits move a submodule pointer, which has no renderer
    paths and is already excluded by ``touching``.
    """
    rows: list[tuple[Commit, Segment, list[str]]] = []
    for seg in SEGMENTS:
        for commit, paths in touching(store, seg):
            rows.append((commit, seg, paths))
    rows.sort(key=lambda row: row[0].instant)
    return rows


def candidates_for(rows, patterns: list[str]) -> list[Candidate]:
    regexes = [re.compile(p, re.IGNORECASE) for p in patterns]
    found: list[Candidate] = []
    for commit, seg, paths in rows:
        hit = [p for p in paths if any(r.search(p) for r in regexes)]
        if hit:
            found.append(Candidate(commit, seg, hit))
    return found


def sweep(rows, every: int) -> list[Candidate]:
    return [Candidate(c, s, p[:3]) for i, (c, s, p) in enumerate(rows) if i % every == 0]


def draw_candidates(
    cands: list[Candidate], *, python: str, worktrees: Worktrees, cache: Path, ids: list[str],
    pick: str | None = None, log=print
) -> None:
    total = len(cands)
    for n, cand in enumerate(cands, 1):
        cand.still = still_for(
            python=python, worktrees=worktrees, cache=cache,
            seg=cand.segment, sha=cand.commit.sha, target_ids=ids, pick=pick,
        )
        mark = cand.still.pixel_hash or "FAILED"
        log(f"  [{n}/{total}] {cand.commit.date[:10]} {cand.commit.sha[:9]} {mark}")


def eras(cands: list[Candidate]) -> list[Candidate]:
    """The first commit of each run of identical pixels. A commit whose still
    failed is skipped: it says nothing about the look."""
    out: list[Candidate] = []
    previous = None
    for cand in sorted(cands, key=lambda c: c.commit.instant):
        if cand.still is None or cand.still.pixel_hash is None:
            continue
        if cand.still.pixel_hash != previous:
            out.append(cand)
            previous = cand.still.pixel_hash
    return out
