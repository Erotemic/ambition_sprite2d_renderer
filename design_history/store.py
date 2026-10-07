"""The git side: where each stretch of the renderer's history lives.

The renderer's history is three stretches that were never one repository:

* ``A00`` — the first generators (``proc2d_character_lab``), May 3-7 2026.
* ``A0`` — the renderer was a subdirectory of the main repository
  (``tools/ambition_sprite2d_renderer/``), April-June 2026. After the split the
  main repository only moves a submodule pointer, which is not content.
* ``R0`` — the renderer's own repository, epoch 0 (June-September 2026).
* ``R1`` — the active renderer repository, epoch 1.

Epoch 0 of both repositories sits in the ``ambition-history`` store as
``refs/epochs/<repo>/000/heads/main``. The active tips are fetched here as
``refs/active/<repo>/main``.
"""

from __future__ import annotations

import dataclasses
import json
import os
import subprocess
from pathlib import Path


@dataclasses.dataclass(frozen=True)
class Segment:
    name: str
    ref: str
    #: Where the renderer's root is inside this segment's tree.
    prefix: str


SEGMENTS = (
    # May 3-7: the first generators, before the lab was promoted into a tool.
    Segment("A00", "refs/epochs/ambition/000/heads/main", "tools/generators/gen2d/"),
    Segment("A0", "refs/epochs/ambition/000/heads/main", "tools/ambition_sprite2d_renderer/"),
    Segment("R0", "refs/epochs/ambition_sprite2d_renderer/000/heads/main", ""),
    Segment("R1", "refs/active/ambition_sprite2d_renderer/main", ""),
)

#: Ledger refs, newest last. The ledger is append-only, so the last one that
#: exists for a repository holds every earlier line.
LEDGER_SOURCES = (
    ("refs/epochs/ambition_sprite2d_renderer/000/heads/main", ".llm_resource_tally/ledger/ledger.jsonl"),
    ("refs/active/ambition_sprite2d_renderer/main", ".llm_resource_tally/ledger/ledger.jsonl"),
    ("refs/epochs/ambition/000/heads/main", ".llm_resource_tally/ledger/ledger.jsonl"),
    ("refs/active/ambition/main", ".llm_resource_tally/ledger/ledger.jsonl"),
)

HISTORY_URL = "https://github.com/Erotemic/ambition-history.git"


def default_store() -> Path:
    """The git directory holding every history stretch."""
    override = os.environ.get("AMBITION_HISTORY_STORE")
    if override:
        return Path(override).expanduser()
    sibling = Path(__file__).resolve().parents[4] / "ambition-history"
    if (sibling / ".git").exists():
        return sibling
    cache = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return cache / "ambition-design-history" / "store"


def git(store: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-C", str(store), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def have_ref(store: Path, ref: str) -> bool:
    return bool(git(store, "for-each-ref", ref, check=False).strip())


def fetch(store: Path, *, active_ambition: Path | None, active_renderer: Path | None) -> None:
    """Make every ref this tool reads exist in ``store``."""
    if not (store / ".git").exists() and not (store / "HEAD").exists():
        store.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q", str(store)], check=True)
    wanted = {
        "refs/epochs/ambition/000/heads/main": HISTORY_URL,
        "refs/epochs/ambition_sprite2d_renderer/000/heads/main": HISTORY_URL,
    }
    for ref, url in wanted.items():
        if not have_ref(store, ref):
            git(store, "fetch", "-q", url, f"{ref}:{ref}")
    for ref, source in (
        ("refs/active/ambition/main", active_ambition),
        ("refs/active/ambition_sprite2d_renderer/main", active_renderer),
    ):
        if source is not None:
            git(store, "fetch", "-q", str(source), f"HEAD:{ref}")


@dataclasses.dataclass(frozen=True)
class Commit:
    sha: str
    segment: str
    date: str          # author date, ISO 8601
    author: str
    subject: str
    body: str

    @property
    def instant(self):
        """The author date as an instant. ``date`` is ISO text with the author's
        own UTC offset, so two commits' strings do not sort as their times do."""
        import datetime

        return datetime.datetime.fromisoformat(self.date)


def commit_info(store: Path, sha: str, segment: str = "") -> Commit:
    out = git(store, "show", "-s", "--format=%H%x1f%aI%x1f%an%x1f%s%x1f%b", sha)
    full, date, author, subject, body = out.rstrip("\n").split("\x1f", 4)
    return Commit(full, segment, date, author, subject, body)


def touching(store: Path, seg: Segment, *, since: str | None = None):
    """Yield ``(Commit, [renderer-relative paths])`` for every commit of ``seg``
    that touches a file under the renderer root, oldest first."""
    fmt = "\x1e%H\x1f%aI\x1f%an\x1f%s\x1f%b\x1f"
    args = ["log", "--reverse", "--name-only", "--no-renames", f"--format={fmt}", seg.ref]
    if since:
        args.append(f"--since={since}")
    args += ["--", seg.prefix or "."]
    out = git(store, *args)
    for chunk in out.split("\x1e")[1:]:
        head, _, names = chunk.partition("\x1f\n")
        parts = head.split("\x1f")
        if len(parts) < 5:
            continue
        sha, date, author, subject, body = parts[0], parts[1], parts[2], parts[3], parts[4]
        paths = [
            n[len(seg.prefix):] for n in names.split("\n")
            if n and n.startswith(seg.prefix) and (not seg.prefix or n != seg.prefix.rstrip("/"))
        ]
        if paths:
            yield Commit(sha, seg.name, date, author, subject, body), paths


def load_ledger(store: Path) -> dict[str, list[dict]]:
    """Measured sessions by commit id. A session names the models it used."""
    by_commit: dict[str, list[dict]] = {}
    seen: set[str] = set()
    for ref, path in LEDGER_SOURCES:
        if not have_ref(store, ref):
            continue
        text = git(store, "show", f"{ref}:{path}", check=False)
        for line in text.splitlines():
            try:
                row = json.loads(line)
            except ValueError:
                continue
            key = f"{row.get('c')}|{row.get('sid')}|{row.get('a')}|{row.get('rec')}"
            if key in seen:
                continue
            seen.add(key)
            by_commit.setdefault(row.get("c", ""), []).append(row)
    return by_commit
