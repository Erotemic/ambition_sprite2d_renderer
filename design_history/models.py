"""The model version of a commit that names a model without its version.

A commit can name a family with no version ("Codex", "Claude Code"), or name
no model at all (Jon's rule: then it is GPT, see `attribution.py`). The
version is the newest one of the family on the commit's date: the newest
version that the history names on or before that date, in any stretch of
the history. A version is known when a ledger row or a trailer signs with
it; a mention in a message can date it earlier (a model a commit names
existed by then), but a mention alone is no version ("GPT56" is a typo).

The timeline is measured from the history store, and cached under the
design-history cache by the tips of its refs.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import re
from pathlib import Path

#: A family name with no version, and the family it means. Claude Code's
#: default model is Opus; Codex is a GPT model.
_BARE = {
    "gpt": "GPT", "codex": "GPT", "openai": "GPT",
    "claude": "Claude Opus", "claude code": "Claude Opus", "opus": "Claude Opus",
    "sonnet": "Claude Sonnet", "fable": "Claude Fable", "haiku": "Claude Haiku",
}
_VERSIONED = re.compile(
    r"^(?:(?P<gpt>GPT)-(?P<gv>\d+(?:\.\d+)?)|(?:Claude )?(?P<cf>Opus|Sonnet|Fable|Haiku) (?P<cv>\d+(?:\.\d+)?))\b(?P<rest>.*)$",
    re.IGNORECASE,
)


def parse(name: str) -> tuple[str | None, tuple[int, ...] | None]:
    """`(family, version)` of a model name; `version` is None for a bare
    family, and both are None for a name that is no known family."""
    m = _VERSIONED.match(name.strip())
    if m:
        if m.group("gpt"):
            return "GPT", tuple(int(x) for x in m.group("gv").split("."))
        return f"Claude {m.group('cf').title()}", tuple(int(x) for x in m.group("cv").split("."))
    bare = re.sub(r"\s+", " ", name.strip().lower())
    bare = re.sub(r"^(?:gpt|openai)[- ]", "gpt ", bare)
    if bare in _BARE:
        return _BARE[bare], None
    if bare.split(" ")[-1] == "codex":  # "GPT Codex", "OpenAI Codex"
        return "GPT", None
    return None, None


def spell(family: str, version: tuple[int, ...]) -> str:
    v = ".".join(str(x) for x in version)
    return f"GPT-{v}" if family == "GPT" else f"{family} {v}"


@dataclasses.dataclass
class Timeline:
    """The first date (ISO) on which the history names each `(family, version)`."""

    first: dict[tuple[str, tuple[int, ...]], str]

    def newest(self, family: str, date: str) -> tuple[int, ...] | None:
        """The newest version of `family` that the history names by `date`."""
        seen = [v for (f, v), d in self.first.items() if f == family and d[:10] <= date[:10]]
        return max(seen) if seen else None

    def earliest(self, family: str) -> tuple[int, ...] | None:
        dated = [(d, v) for (f, v), d in self.first.items() if f == family]
        return min(dated)[1] if dated else None

    def resolve(self, name: str, date: str) -> tuple[str, bool]:
        """`(name, by_date)`: `name` with its version, and True when the
        version came from the date. A date before the family's first named
        version gives `<family> before <that version>`."""
        family, version = parse(name)
        if version is not None or family is None:
            return name, False
        newest = self.newest(family, date)
        if newest is not None:
            return spell(family, newest), True
        first = self.earliest(family)
        return (f"{family} before {spell(family, first)[len(family):].strip(' -')}" if first else family), True

    def as_json(self) -> list:
        return sorted([f, list(v), d] for (f, v), d in self.first.items())

    @classmethod
    def from_json(cls, rows: list) -> "Timeline":
        return cls({(f, tuple(v)): d for f, v, d in rows})


def measure(commits, ledger: dict[str, list[dict]]) -> Timeline:
    """The timeline of `commits` (each `Commit`): the first date that names
    each version that a ledger row or a trailer signs with."""
    from .attribution import named_models, signed_models  # noqa: PLC0415

    first: dict[tuple[str, tuple[int, ...]], str] = {}
    signed: set[tuple[str, tuple[int, ...]]] = set()
    for commit in commits:
        names = named_models(commit, ledger)
        sign = set(signed_models(commit, ledger))
        for name in names:
            family, version = parse(name)
            if version is None:
                continue
            key = (family, version)
            if name in sign:
                signed.add(key)
            if key not in first or commit.date < first[key]:
                first[key] = commit.date
    return Timeline({k: d for k, d in first.items() if k in signed})


_REFS = ("refs/epochs/ambition/000/heads/main", "refs/epochs/ambition_sprite2d_renderer/000/heads/main",
         "refs/active/ambition_sprite2d_renderer/main", "refs/active/ambition/main")


def from_store(store: Path, ledger: dict[str, list[dict]], cache: Path | None = None) -> Timeline:
    """The timeline of every ref of the history store, cached by their tips."""
    from .store import Commit, git  # noqa: PLC0415

    tips = [git(store, "rev-parse", "-q", "--verify", ref, check=False).strip() for ref in _REFS]
    key = hashlib.sha1(("|".join(tips) + f"|{len(ledger)}").encode()).hexdigest()[:16]
    hit = cache / f"models-{key}.json" if cache else None
    if hit and hit.exists():
        return Timeline.from_json(json.loads(hit.read_text()))
    commits = []
    for ref, tip in zip(_REFS, tips):
        if not tip:
            continue
        out = git(store, "log", ref, "--format=%H%x00%aI%x00%an%x00%s%x00%b%x01", check=False)
        for rec in out.split("\x01"):
            rec = rec.strip("\n")
            if rec:
                sha, date, author, subject, body = rec.split("\x00", 4)
                commits.append(Commit(sha, "", date, author, subject, body))
    timeline = measure(commits, ledger)
    if hit:
        hit.parent.mkdir(parents=True, exist_ok=True)
        hit.write_text(json.dumps(timeline.as_json()))
    return timeline
