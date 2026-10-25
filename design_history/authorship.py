"""Who wrote a character's generator, line by line, at one commit.

`attribution.attribute` says who made ONE commit. The commit that pins an era
is often not the commit that made the look: it can be the last commit before a
redesign, a refactor, a merge, or the import that started an epoch. So the
authorship of an era is measured on the generator itself: `git blame` each
generator file at the era's commit, attribute the commit of each line, and
count lines.

The history crosses two imports. The first commit of the active renderer
(`R1`, "Start git epoch 1") is a copy of the tip of `R0`, and the commit that
brought the renderer package into `R0` ("Initial commit", after the
repository host's LICENSE commit) is a copy of the renderer subdirectory of
the main repository (`A0`).
A line that blame gives to an import commit is looked up, by its text, in the
blame of the same file at the commit before the import. A line that is not
found there stays with the import commit and counts as unknown.

The result is evidence about sessions, not proof about pixels (see
`attribution.py`). Each share keeps its basis, so a reader can discount it.
"""

from __future__ import annotations

import collections
import dataclasses
import hashlib
import json
import re
from pathlib import Path

from . import models
from .attribution import Attribution, attribute
from .store import commit_info, git

#: The suffixes of a generator: code, job configs, SVG art and rig documents.
SOURCE_SUFFIXES = (".py", ".yaml", ".yml", ".svg", ".json")
#: Renderer-relative paths that are never a generator.
_VERSION = re.compile(r"_v(\d+)(?![a-z0-9])")
_NOT_GENERATOR = re.compile(r"(^|/)(tests?|docs|generated|design_history|\.cache)/|\.md$")

#: Where the renderer root is in each history stretch, newest first.
_PREFIXES = ("", "tools/ambition_sprite2d_renderer/", "tools/generators/gen2d/")
#: The renderer package: the commit that first adds it to a stretch is that stretch's import.
_PACKAGE = "ambition_sprite2d_renderer"
#: Part of each cached blame's name: a change to how imports are followed
#: (`roots`) changes the lines, so it changes this.
_LINES_VERSION = "v2"
_IMPORTS = {
    # first commit of the stretch -> (ref of the stretch it copies, prefix there)
    "R1": ("refs/epochs/ambition_sprite2d_renderer/000/heads/main", ""),
    "R0": ("refs/epochs/ambition/000/heads/main", "tools/ambition_sprite2d_renderer/"),
}


@dataclasses.dataclass(frozen=True)
class Share:
    """Lines of the generator that one author made."""

    who: str          # "Claude Opus 5.5", "GPT (inferred)", "unknown"
    kind: str         # model | inferred | unknown
    basis: str        # the strongest `attribution` basis among its commits
    lines: int
    commits: tuple[str, ...]

    def as_dict(self) -> dict:
        return dataclasses.asdict(self)


#: A drawing; every other generator file is code or data (a config, a rig).
ART_SUFFIXES = (".svg",)


@dataclasses.dataclass
class Authorship:
    commit: str
    files: dict[str, int]                 # renderer-relative path -> lines
    shares: list[Share]                   # every file
    parts: dict[str, list[Share]]         # "art" (drawings) and "code" (the rest)
    found_by: str = "named"               # how the files were found (`generator_files`)

    @property
    def lines(self) -> int:
        return sum(self.files.values())

    def known_fraction(self) -> float:
        known = sum(s.lines for s in self.shares if s.kind != "unknown")
        return known / self.lines if self.lines else 0.0

    def confidence(self) -> str:
        """`high`: the files name the target, at least 90% of the lines have a
        named author and the main author is declared or measured. `medium`: at
        least half of the lines have a named author, and the files were found
        by name or by a helper the lineage names. `low`: otherwise. `none`: no
        generator file was found."""
        if not self.lines:
            return "none"
        known = self.known_fraction()
        top = self.shares[0] if self.shares else None
        if self.found_by == "named" and known >= 0.9 and top and top.basis in ("measured", "declared"):
            return "high"
        return "medium" if known >= 0.5 and self.found_by in ("named", "helper") else "low"

    def as_dict(self) -> dict:
        return {
            "commit": self.commit,
            "lines": self.lines,
            "files": self.files,
            "found_by": self.found_by,
            "shares": [s.as_dict() for s in self.shares],
            "parts": {k: [s.as_dict() for s in v] for k, v in self.parts.items()},
            "known_fraction": round(self.known_fraction(), 3),
            "confidence": self.confidence(),
        }


_BASIS_RANK = {"measured": 0, "declared": 1, "message": 2, "inferred": 3, "unknown": 4}


def describe(who: Attribution) -> tuple[str, str]:
    """`(name, kind)` of one commit's author for a share."""
    if who.basis == "inferred":
        # No model signed the commit (see `attribution.py`): the share says
        # so in its name, apart from the GPT commits that name themselves.
        return ", ".join(who.models) + " (inferred)", "inferred"
    if who.models:
        return ", ".join(who.models), "model"
    return "unknown", "unknown"


class Blamer:
    """Blames files in the history store, with a cache on disk. A blame of a
    fixed commit never changes, so the cache never goes stale."""

    def __init__(self, store: Path, cache: Path | None, ledger: dict | None = None, *, local: Path | None = None):
        """`local` is a renderer checkout for commits that the store does not
        have yet (work after the last `fetch`)."""
        self.store = store
        self.repos = [store, *([local] if local else [])]
        self.cache = cache / "blame" if cache else None
        self.ledger = ledger or {}
        # A model named without its version takes the newest on the commit's date.
        self.timeline = models.from_store(store, self.ledger, cache)
        self._who: dict[str, Attribution] = {}
        self._roots: dict[str, str] | None = None
        self._repo_of: dict[str, Path | None] = {}

    def repo(self, sha: str) -> Path | None:
        """The first repository that has commit `sha`."""
        if sha not in self._repo_of:
            self._repo_of[sha] = next(
                (r for r in self.repos if git(r, "rev-parse", "--verify", "-q", f"{sha}^{{commit}}", check=False).strip()),
                None,
            )
        return self._repo_of[sha]

    # -- where things are ---------------------------------------------------------------
    def prefix(self, sha: str) -> str | None:
        """The renderer root inside `sha`'s tree."""
        for prefix, probe in zip(_PREFIXES, ("ambition_sprite2d_renderer", *(p.rstrip("/") for p in _PREFIXES[1:]))):
            if git(self.repo(sha) or self.store, "cat-file", "-t", f"{sha}:{probe}", check=False).strip() == "tree":
                return prefix
        return None

    def roots(self) -> dict[str, str]:
        """Import commit -> the name of the stretch it starts. The import is
        the commit that brought the renderer package into the repository: the
        root of `R1`, and in `R0` the commit after the host's LICENSE root."""
        if self._roots is None:
            self._roots = {}
            starts = [("R1", self.store, "refs/active/ambition_sprite2d_renderer/main"),
                      ("R0", self.store, "refs/epochs/ambition_sprite2d_renderer/000/heads/main"),
                      *(("R1", repo, "HEAD") for repo in self.repos[1:])]
            for name, repo, ref in starts:
                first = git(repo, "rev-list", "--reverse", ref, "--", _PACKAGE, check=False).split()
                if first:
                    self._roots.setdefault(first[0], name)
        return self._roots

    def before_import(self, root: str, path: str) -> tuple[str, str] | None:
        """The commit and path that an import commit copied `path` from."""
        ref, prefix = _IMPORTS[self.roots()[root]]
        if not git(self.store, "for-each-ref", ref, check=False).strip():
            return None
        date = git(self.store, "show", "-s", "--format=%aI", root).strip()
        full = prefix + path
        sha = git(self.store, "log", "-1", "--format=%H", f"--before={date}", ref, "--", full, check=False).strip()
        if not sha or git(self.store, "cat-file", "-t", f"{sha}:{full}", check=False).strip() != "blob":
            return None
        return sha, full

    # -- blame --------------------------------------------------------------------------
    def _raw(self, sha: str, full: str) -> list[tuple[str, str]]:
        """`(commit, text)` of each line of `full` at `sha`, as git blames it."""
        out = git(self.repo(sha) or self.store, "blame", "-w", "--line-porcelain", sha, "--", full, check=False)
        lines: list[tuple[str, str]] = []
        commit = None
        for line in out.splitlines():
            if line.startswith("\t"):
                lines.append((commit or "", line[1:]))
                commit = None
            elif commit is None and re.match(r"^[0-9a-f]{40} ", line):
                commit = line.split(" ", 1)[0]
        return lines

    def lines(self, sha: str, full: str, depth: int = 0) -> list[str]:
        """The commit of each line of `full` at `sha`, followed through imports."""
        # The blame of a file is the same at every commit after the last one
        # that changed it, so that commit is the cache key: a new commit that
        # does not touch the file costs no new blame.
        sha = self.last_change(sha, full)
        key = None
        if self.cache:
            key = self.cache / f"{_LINES_VERSION}-{sha[:16]}-{hashlib.sha1(full.encode()).hexdigest()[:16]}.json"
            if key.exists():
                return json.loads(key.read_text())
        raw = self._raw(sha, full)
        roots = self.roots()
        imported = {c for c, _ in raw if c in roots}
        if imported and depth < 3:
            rel_prefix = self.prefix(sha) or ""
            path = full[len(rel_prefix):]
            pools: dict[str, dict[str, collections.deque]] = {}
            for root in imported:
                before = self.before_import(root, path)
                pool: dict[str, collections.deque] = collections.defaultdict(collections.deque)
                if before:
                    old_sha, old_full = before
                    texts = [t for _, t in self._raw(old_sha, old_full)]
                    for commit, text in zip(self.lines(old_sha, old_full, depth + 1), texts):
                        pool[text].append(commit)
                pools[root] = pool
            raw = [(pools[c][t].popleft() if c in pools and pools[c].get(t) else c, t) for c, t in raw]
        result = [c for c, _ in raw]
        if key:
            key.parent.mkdir(parents=True, exist_ok=True)
            key.write_text(json.dumps(result))
        return result

    def last_change(self, sha: str, full: str) -> str:
        """The last commit at or before `sha` that changed `full`. It never
        changes for a given pair, so it is cached on disk."""
        name = hashlib.sha1(f"{sha}:{full}".encode()).hexdigest()[:24]
        hit = self.cache / "last" / name if self.cache else None
        if hit and hit.exists():
            return hit.read_text().strip() or sha
        last = git(self.repo(sha) or self.store, "rev-list", "-1", sha, "--", full, check=False).strip()
        if hit and last:
            hit.parent.mkdir(parents=True, exist_ok=True)
            hit.write_text(last)
        return last or sha

    def who(self, sha: str) -> Attribution:
        if sha not in self._who:
            if sha in self.roots():
                self._who[sha] = Attribution((), "unknown", "an import commit: the line was not found before it")
            else:
                self._who[sha] = attribute(commit_info(self.repo(sha) or self.store, sha), self.ledger, self.timeline)
        return self._who[sha]

    def authorship(self, sha: str, paths: list[str], found_by: str = "named") -> Authorship:
        """Line shares of the renderer-relative `paths` at `sha`."""
        prefix = self.prefix(sha) or ""
        files: dict[str, int] = {}
        groups: dict[str, collections.Counter] = {"all": collections.Counter(), "art": collections.Counter(), "code": collections.Counter()}
        for path in paths:
            commits = self.lines(sha, prefix + path)
            if not commits:
                continue
            files[path] = len(commits)
            part = "art" if path.endswith(ART_SUFFIXES) else "code"
            groups["all"].update(commits)
            groups[part].update(commits)
        shares = {k: self._shares(v) for k, v in groups.items()}
        return Authorship(sha, files, shares["all"], {"art": shares["art"], "code": shares["code"]}, found_by)

    def _shares(self, counts: collections.Counter) -> list[Share]:
        per: dict[tuple[str, str], list] = {}
        for commit, n in counts.items():
            who = self.who(commit)
            name, kind = describe(who)
            slot = per.setdefault((name, kind), [0, [], "unknown"])
            slot[0] += n
            slot[1].append((n, commit))
            if _BASIS_RANK.get(who.basis, 9) < _BASIS_RANK.get(slot[2], 9):
                slot[2] = who.basis
        shares = [
            Share(name, kind, basis, n, tuple(c for _, c in sorted(commits, reverse=True)[:5]))
            for (name, kind), (n, commits, basis) in per.items()
        ]
        shares.sort(key=lambda s: (-s.lines, s.who))
        return shares


def names(path: str, ident: str) -> bool:
    """True when a component of `path` starts with `ident` as a whole word:
    `alice` names `configs/review/alice.yaml`, `_toon_presets/alice.py` and
    `alice_paper_doll.py`, not `player_alice.py` or `alice2.py`. A leading
    `_` (a private helper module) and `-` for `_` are ignored."""
    for part in path.split("/"):
        part = part.lstrip("_").replace("-", "_")
        if part.startswith(ident) and not part[len(ident):len(ident) + 1].isalnum():
            return True
    return False


def generator_files(
    store: Path, sha: str, prefix: str, target: str, *, aliases: list[str], others: set[str],
    patterns: list[str] | None = None,
) -> tuple[list[str], str]:
    """The renderer-relative files that draw `target` at `sha`, found by name,
    and how they were found.

    `named`: a component of the path starts with the target or one of its
    `aliases` (old names of the same character), and not with a longer target
    of `others` (`alice_v2` is not `alice`). The lineage's `patterns` add the
    helpers they match that name no other target, except a family the target
    belongs to (`ninja_heavy.py` draws `ninja_heavy_eye_band`).
    `helper`: no file names the target, so the helpers alone.
    `pattern`: no helper either, so every file the patterns match, except
    the files of another generation of the character.
    `none`: nothing. It is a heuristic, and the result says which rung found it."""
    listed = git(store, "ls-tree", "-r", "--name-only", sha, "--", prefix or ".", check=False).splitlines()
    words = [target, *aliases]
    longer = {o for o in others if o not in words and any(o.startswith(w + "_") for w in words)}
    # A family the target belongs to: `ninja_heavy` for `ninja_heavy_eye_band`.
    # An older generation is not one: `paul_diracula` for `paul_diracula_v2`.
    family = {o for o in others if target.startswith(o + "_") and not re.fullmatch(r"v\d+", target[len(o) + 1:])}
    strangers = {o for o in others if o not in words and o not in family}
    # Another generation of the same character draws another look.
    base = re.sub(r"_v\d+$", "", target)
    generations = {o for o in others if o != target and re.sub(r"_v\d+$", "", o) == base}
    extra = [re.compile(p, re.IGNORECASE) for p in patterns or []]
    named_files, helpers, matched = [], [], []
    for name in listed:
        rel = name[len(prefix):] if prefix and name.startswith(prefix) else name
        if not rel.endswith(SOURCE_SUFFIXES) or _NOT_GENERATOR.search(rel):
            continue
        if any(names(rel, o) for o in longer):
            continue
        if any(names(rel, w) for w in words):
            named_files.append(rel)
        elif any(e.search(rel) for e in extra) and not any(names(rel, o) for o in generations):
            matched.append(rel)
            # A versioned helper (`_runge_kutta_v2.py`) draws that version only.
            if not any(names(rel, o) for o in strangers) and set(_VERSION.findall(rel)) <= set(_VERSION.findall(target)):
                helpers.append(rel)
    if named_files:
        return named_files + helpers, "named"
    if helpers:
        return helpers, "helper"
    return (matched, "pattern") if matched else ([], "none")


def specific_inputs(records: dict[str, dict], unit: str, *, at_most: int = 3) -> list[str]:
    """The inputs of `unit`'s provenance record that at most `at_most` records
    read: its own generator files, without the shared renderer modules.
    Paths are renderer-relative."""
    count: collections.Counter = collections.Counter()
    for record in records.values():
        count.update({i["path"] for i in record.get("inputs", [])})
    prefix = "tools/ambition_sprite2d_renderer/"
    out = []
    for item in records.get(unit, {}).get("inputs", []):
        path = item["path"]
        if count[path] <= at_most and path.startswith(prefix) and path.endswith(SOURCE_SUFFIXES):
            out.append(path[len(prefix):])
    return out


def era_generator(store: Path, sha: str, prefix: str, spec: dict, era: dict, current: set[str]) -> tuple[str, list[str], str]:
    """The target that draws `era` at `sha`, its generator files and how they
    were found (see `generator_files`).

    An era with an `id` is that target. Otherwise the lineage's `ids` are
    tried in order, as the still renderer does: the first that a file names
    wins, and only when none is named does the first id take its helpers. A
    lineage id that is not a `current` target is an old name of the character
    (`alice_cryptographer`) and counts as an alias; a current target is a
    different generation and does not."""
    from .characters import lineage_targets

    claimed = lineage_targets(spec)
    ids = [str(era["id"])] if era.get("id") else [str(i) for i in spec.get("ids") or []]
    retired = [i for i in claimed if i not in current]
    found = []
    for target in ids:
        files, how = generator_files(
            store, sha, prefix, target,
            aliases=[a for a in retired if a != target], others=current | set(claimed),
            patterns=spec.get("paths"),
        )
        if how == "named":
            return target, files, how
        found.append((target, files, how))
    for target, files, how in found:
        if files:
            return target, files, how
    return (ids[0] if ids else ""), [], "none"
