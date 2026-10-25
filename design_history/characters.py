"""From a character to its lineage, and from an era to its target and commit.

A character has three names, and each names it in a different place:

* a **lineage** name (`lineages.yaml`): the character as the player knows it;
* a **renderer target** (`alice`, `paul_diracula_v2`): the generator of one
  sheet. A lineage claims the targets in its `ids` and in the `id` of each era;
* a **catalog id** (`npc_paul_diracula`, `stochastic_parrot`): a row of a game's
  `character_catalog.ron`, or a boss key of `boss_art_keys.ron`. A row names
  the sheet it draws, and the actor sidecar of a sheet names its catalog id.

This module joins the three. It reads the tracked game data and the published
sidecars as text, and it is read-only: it is not a registry and nothing in the
game reads it. The sheet-to-target step reads the art provenance records
(`asset_provenance/sprites/*.json`) when they exist, and else the sheet's
file name.
"""

from __future__ import annotations

import dataclasses
import json
import re
from pathlib import Path

_SHEET = re.compile(r'"(?:sprites/)?((?:[a-z0-9_]+/)*[a-z0-9_]+?)_spritesheet\.(?:ron|png)"')
_ROW = re.compile(r'^ {8}"([^"]+)"\s*:\s*\(')
_FIELD = {
    "form_of": re.compile(r'^\s*form_of:\s*Some\("([^"]+)"\)'),
    "derived_from": re.compile(r'^\s*derived_from:\s*Some\("([^"]+)"\)'),
}
_VERSIONED = re.compile(r"^(?P<base>.+?)_v(?P<n>\d+)$")


def repo_root() -> Path:
    """The game repository that holds this renderer checkout."""
    return Path(__file__).resolve().parents[3]


def asset_root(repo: Path) -> Path:
    return repo / "crates" / "ambition_platformer2d_actor_monolith" / "assets"


def lineage_targets(spec: dict) -> list[str]:
    """Every target a lineage claims: its `ids`, then each era's `id`, once."""
    out: list[str] = []
    for ident in [*(spec.get("ids") or []), *(era.get("id") for era in spec.get("eras") or [])]:
        if ident and ident not in out:
            out.append(str(ident))
    return out


def by_target(lineages: dict) -> dict[str, list[str]]:
    """Target id -> the lineages that claim it (more than one when a sheet is
    shared, such as the giant gnu under GNU-ton)."""
    out: dict[str, list[str]] = {}
    for name, spec in lineages.items():
        for ident in lineage_targets(spec):
            out.setdefault(ident, []).append(name)
    return out


def era_target(spec: dict, era: dict, known: set[str] | None = None) -> str:
    """The target that draws `era`: its own `id`, else the first lineage id
    that is a current target (`known`), else the first lineage id."""
    if era.get("id"):
        return str(era["id"])
    ids = [str(i) for i in spec.get("ids") or []]
    if known:
        for ident in ids:
            if ident in known:
                return ident
    return ids[0] if ids else ""


def era_ids(name: str, spec: dict, era: dict) -> list[str]:
    """The target ids the still renderer tries for `era`, in order."""
    return [str(era["id"])] if era.get("id") else [str(i) for i in spec.get("ids") or [name]]


@dataclasses.dataclass
class CatalogRow:
    id: str
    file: str
    line: int
    sheets: list[str] = dataclasses.field(default_factory=list)
    form_of: str | None = None
    derived_from: str | None = None
    kind: str = "character"  # character | boss


def catalog_rows(repo: Path) -> dict[str, CatalogRow]:
    """The rows of every game's `character_catalog.ron` and the boss keys of
    `boss_art_keys.ron`, each with the sheets it names."""
    rows: dict[str, CatalogRow] = {}
    for path in sorted(repo.glob("game/*/assets/data/character_catalog.ron")):
        rel = path.relative_to(repo).as_posix()
        inside, row = False, None
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            code = line.split("//", 1)[0]
            if re.match(r"^ {4}characters:\s*\{", code):
                inside = True
                continue
            if inside and re.match(r"^ {4}\}", code):
                inside, row = False, None
                continue
            if not inside:
                continue
            m = _ROW.match(code)
            if m:
                row = rows.setdefault(m.group(1), CatalogRow(m.group(1), rel, number))
                continue
            if row is None:
                continue
            row.sheets += [s for s in _SHEET.findall(code) if s not in row.sheets]
            for field, regex in _FIELD.items():
                hit = regex.match(code)
                if hit:
                    setattr(row, field, hit.group(1))
    keys = repo / "game" / "ambition_content" / "assets" / "data" / "boss_art_keys.ron"
    if keys.is_file():
        rel = keys.relative_to(repo).as_posix()
        for number, line in enumerate(keys.read_text(encoding="utf-8").splitlines(), 1):
            m = re.match(r'^\s*"([a-z0-9_]+)":\s*"([^"]+_spritesheet\.png)"', line.split("//", 1)[0])
            if m:
                ident = f"boss:{m.group(1)}"
                rows[ident] = CatalogRow(ident, rel, number, _SHEET.findall(f'"{m.group(2)}"'), kind="boss")
    return rows


def sheet_owners(repo: Path) -> dict[str, str]:
    """Published sheet key (`giant_gnu`, `gnu_ton_boss/giant_gnu`) -> the target
    whose provenance record lists it."""
    out: dict[str, str] = {}
    records = repo / "crates" / "ambition_platformer2d_actor_monolith" / "asset_provenance" / "sprites"
    for path in sorted(records.glob("*.json")) if records.is_dir() else []:
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        unit = record.get("unit") or path.stem
        for row in record.get("outputs", []):
            m = re.fullmatch(r"(.+)_spritesheet\.(?:ron|png)", row.get("path", ""))
            if m:
                out.setdefault(m.group(1), unit)
    return out


def sidecar_characters(repo: Path, owners: dict[str, str] | None = None) -> dict[str, str]:
    """Target -> the catalog id its published actor sidecar names. The target
    is the one whose provenance record publishes the sheet (`owners`); the
    sidecar's `renderer_target` only when no record does, because an old
    sidecar can name the rig it was built on (the first dividing mite names
    `robot`)."""
    owners = sheet_owners(repo) if owners is None else owners
    out: dict[str, str] = {}
    sprites = asset_root(repo) / "sprites"
    for path in sorted(sprites.glob("*_actor.ron")) if sprites.is_dir() else []:
        text = path.read_text(encoding="utf-8", errors="replace")
        cid = re.search(r'\bcharacter_id:\s*(?:Some\()?"([^"]+)"', text)
        target = re.search(r'\brenderer_target:\s*(?:Some\()?"([^"]+)"', text)
        if cid:
            sheet = path.name[: -len("_actor.ron")]
            out.setdefault(owners.get(sheet) or (target.group(1) if target else sheet), cid.group(1))
    return out


@dataclasses.dataclass
class Join:
    """The three names of each character, joined both ways."""

    lineages: dict
    targets: dict[str, list[str]]           # target -> lineages
    rows: dict[str, CatalogRow]             # catalog id -> row
    row_targets: dict[str, list[str]]       # catalog id -> targets that draw it
    target_rows: dict[str, list[str]]       # target -> catalog ids

    def find(self, name: str) -> list[tuple[str, str]]:
        """The lineages of `name` (a lineage, a target or a catalog id), each
        with the way it was found."""
        hits: list[tuple[str, str]] = []

        def add(lineage: str, via: str) -> None:
            if lineage not in [h[0] for h in hits]:
                hits.append((lineage, via))

        if name in self.lineages:
            add(name, "lineage name")
        for lineage in self.targets.get(name, []):
            add(lineage, f"target {name}")
        for target in self.row_targets.get(name, []):
            for lineage in self.targets.get(target, []):
                add(lineage, f"catalog {name} -> target {target}")
        row = self.rows.get(name)
        if row and row.form_of:
            for lineage, via in self.find(row.form_of):
                add(lineage, f"a look (form_of) of {row.form_of}: {via}")
        return hits


def join(lineages: dict, repo: Path | None = None) -> Join:
    repo = repo or repo_root()
    rows = catalog_rows(repo)
    owners = sheet_owners(repo)
    row_targets: dict[str, list[str]] = {}
    for ident, row in rows.items():
        for sheet in row.sheets:
            target = owners.get(sheet) or sheet.rsplit("/", 1)[-1]
            row_targets.setdefault(ident, [])
            if target not in row_targets[ident]:
                row_targets[ident].append(target)
    for target, cid in sidecar_characters(repo, owners).items():
        if cid in rows and target not in row_targets.setdefault(cid, []):
            row_targets[cid].append(target)
    target_rows: dict[str, list[str]] = {}
    for ident, targets in row_targets.items():
        for target in targets:
            target_rows.setdefault(target, []).append(ident)
    return Join(lineages, by_target(lineages), rows, row_targets, target_rows)


def versioned_pairs(targets: set[str]) -> list[tuple[str, str]]:
    """`(target, base)` for each `<base>_vN` target whose base (or `_v(N-1)`)
    is also a target: a redesign published beside the old look."""
    out = []
    for target in sorted(targets):
        m = _VERSIONED.match(target)
        if not m:
            continue
        n = int(m.group("n"))
        for base in (*(f"{m.group('base')}_v{k}" for k in range(n - 1, 1, -1)), m.group("base")):
            if base in targets:
                out.append((target, base))
                break
    return out
