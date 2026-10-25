"""``python -m design_history`` — run from ``tools/ambition_sprite2d_renderer``."""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import sys
from pathlib import Path

import yaml

from . import census as census_mod
from . import models
from . import characters as characters_mod
from . import survey as survey_mod
from .attribution import attribute
from .authorship import Blamer
from .progression import Tile, compose, stack
from .store import (
    SEGMENTS, commit_info, default_store, fetch, git, load_ledger,
)
from .stills import Worktrees, default_cache, still_for
from .view import lineage_view

HERE = Path(__file__).resolve().parent
LINEAGES = HERE / "lineages.yaml"
OUT = HERE.parent / "generated" / "design_history"


def load_lineages() -> dict:
    return yaml.safe_load(LINEAGES.read_text(encoding="utf-8"))["lineages"]


def _python(args) -> str:
    return args.python or os.environ.get("AMBITION_SPRITE_PYTHON") or sys.executable


def _context(args):
    store = Path(args.store).expanduser() if args.store else default_store()
    cache = default_cache()
    return store, cache, Worktrees(store, cache)


def cmd_fetch(args) -> int:
    store, _, _ = _context(args)
    root = HERE.parents[2]
    fetch(
        store,
        active_ambition=root if (root / ".git").exists() else None,
        active_renderer=HERE.parent if (HERE.parent / ".git").exists() else None,
    )
    print(f"history store ready: {store}")
    return 0


def _short(text: str, n: int = 52) -> str:
    return text if len(text) <= n else text[: n - 1] + "…"


def cmd_survey(args) -> int:
    store, cache, worktrees = _context(args)
    ledger = load_ledger(store)
    rows = survey_mod.history(store)
    names = list(load_lineages()) if args.all else args.lineage
    lineages = load_lineages()
    OUT.joinpath("survey").mkdir(parents=True, exist_ok=True)
    try:
        for name in names:
            spec = lineages.get(name, {})
            ids = args.ids.split(",") if args.ids else spec.get("ids", [name])
            patterns = args.paths.split(",") if args.paths else spec.get("paths", [name])
            cands = survey_mod.candidates_for(rows, patterns)
            if args.sweep:
                seen = {c.commit.sha for c in cands}
                cands += [c for c in survey_mod.sweep(rows, args.sweep) if c.commit.sha not in seen]
            print(f"{name}: {len(cands)} candidate commits, ids={ids}")
            survey_mod.draw_candidates(
                cands, python=_python(args), worktrees=worktrees, cache=cache, ids=ids,
                pick=spec.get("pick"),
            )
            found = survey_mod.eras(cands)
            tiles = []
            for cand in found:
                who = attribute(cand.commit, ledger, models.from_store(store, ledger, default_cache())).label()
                tiles.append(Tile(
                    cand.still.path,
                    [f"{cand.commit.date[:10]} {cand.commit.sha[:9]}",
                     _short(cand.commit.subject, 60), _short(who, 60),
                     f"{cand.segment.name}"],
                ))
            print(f"{name}: {len(found)} distinct looks")
            for cand in found:
                print(f"  {cand.commit.date[:10]} {cand.commit.sha}  {_short(cand.commit.subject, 70)}")
            if tiles:
                compose(f"{name} — survey", tiles, per_row=spec.get("per_row", 6), tile_w=spec.get("tile_w", 190)).save(OUT / "survey" / f"{Path(name).name}.png")
    finally:
        if not args.keep_worktrees:
            worktrees.remove()
    return 0


def _resolve(store: Path, rows_index: dict, sha: str):
    for row_sha, row in rows_index.items():
        if row_sha.startswith(sha):
            return row
    raise SystemExit(f"commit {sha} touches no renderer path in any segment")


def cmd_build(args) -> int:
    store, cache, worktrees = _context(args)
    ledger = load_ledger(store)
    lineages = load_lineages()
    index = {c.sha: (c, seg) for c, seg, _ in survey_mod.history(store)}
    names = list(lineages) if args.all else args.lineage
    OUT.mkdir(parents=True, exist_ok=True)
    groups: dict[str, list] = {}
    try:
        for name in names:
            spec = lineages[name]
            tiles: list[Tile] = []
            for era in spec.get("eras", []):
                commit, seg = _resolve(store, index, str(era["commit"]))
                ids = characters_mod.era_ids(name, spec, era)
                still = still_for(
                    python=_python(args), worktrees=worktrees, cache=cache,
                    seg=seg, sha=commit.sha, target_ids=ids,
                    pick=era.get("pick", spec.get("pick")),
                )
                who = attribute(commit, ledger, models.from_store(store, ledger, default_cache()))
                lines = [era["label"], f"{commit.date[:10]} · {commit.sha[:9]}"]
                if era.get("as"):
                    lines.insert(1, f"called: {era['as']}")
                lines.append(who.label())
                tiles.append(Tile(still.path, lines))
                if not still.path:
                    print(f"  {name}: {era['label']}: no render ({still.failure[:100]})")
            if tiles:
                title = f"{spec.get('name', name)} — {spec.get('summary', 'design history')}"
                sheet = compose(title, tiles, per_row=spec.get("per_row", args.per_row), tile_w=spec.get("tile_w", 190))
                sheet.save(OUT / f"{name}.png")
                print(f"{name}: {len(tiles)} eras -> {OUT / (name + '.png')}")
                if spec.get("group"):
                    groups.setdefault(spec["group"], []).append(sheet)
        for group, sheets in groups.items():
            stack(f"{group} — design history", sheets).save(OUT / f"group_{group}.png")
            print(f"group {group}: {len(sheets)} lineages -> {OUT / ('group_' + group + '.png')}")
    finally:
        if not args.keep_worktrees:
            worktrees.remove()
    return 0


def cmd_list(args) -> int:
    for name, spec in load_lineages().items():
        print(f"{name:28s} {len(spec.get('eras', [])):2d} eras  {spec.get('summary', '')}")
    return 0


def cmd_attribution(args) -> int:
    store, _, _ = _context(args)
    ledger = load_ledger(store)
    commit = commit_info(store, git(store, "rev-parse", args.commit).strip())
    who = attribute(commit, ledger, models.from_store(store, ledger, default_cache()))
    print(json.dumps({"commit": commit.sha, "date": commit.date, "models": who.models,
                      "basis": who.basis, "note": who.note}, indent=2))
    return 0


def _store_or_none(args) -> Path | None:
    store, _, _ = _context(args)
    return store if git(store, "for-each-ref", "refs/active", check=False).strip() else None


def cmd_character(args) -> int:
    """The lineages of a catalog id, a target or a lineage name, with each
    era's commit, target and authorship."""
    lineages = load_lineages()
    join = characters_mod.join(lineages)
    hits = join.find(args.name)
    if not hits:
        print(f"{args.name}: no lineage claims it (not a lineage, a lineage target or a catalog row that draws one)")
        return 1
    store = _store_or_none(args)
    if store is None:
        print("note: no history store; run `python -m design_history fetch` for commits and authorship", file=sys.stderr)
    ledger = load_ledger(store) if store else {}
    blamer = Blamer(store, default_cache(), ledger) if store and not args.no_blame else None
    current = set(census_mod.registry(_python(args)))
    views = []
    for name, via in hits:
        view = lineage_view(name, lineages[name], store=store, cache=default_cache(), blamer=blamer, current=current, ledger=ledger)
        view["found_via"] = via
        views.append(view)
    if args.json:
        print(json.dumps(views, indent=2))
        return 0
    for view in views:
        print(f"{view['name']} [{view['lineage']}] — found via {view['found_via']}")
        print(f"  targets: {', '.join(view['targets'])} (current: {', '.join(view['current_targets']) or 'none'})")
        catalog = sorted({row for t in view["targets"] for row in join.target_rows.get(t, [])})
        if catalog:
            print(f"  catalog: {', '.join(catalog)}")
        for era in view["eras"]:
            date = era.get("date", "")[:10]
            print(f"  - {date or '?':10s} {era['commit']:12s} {era.get('target') or '/'.join(era['ids'])}: {era['label']}")
            if era.get("pin"):
                print(f"      commit made by: {era['pin']['label']}")
            gen = era.get("generator")
            if gen:
                print(f"      generator: {len(gen['files'])} files, {gen['lines']} lines, found {gen['found_by']}, confidence {gen['confidence']}")
                for part, shares in gen["parts"].items():
                    total = sum(s["lines"] for s in shares)
                    if total:
                        text = ", ".join(f"{s['who']} {100 * s['lines'] / total:.0f}%" for s in shares[:3])
                        print(f"        {part}: {text}")
            if era.get("still"):
                print(f"      still: {era['still']}")
    return 0


def cmd_census(args) -> int:
    lineages = load_lineages()
    targets = census_mod.registry(_python(args))
    repo = characters_mod.repo_root()
    out = {"coverage": census_mod.coverage(lineages, targets, repo),
           "skin_cost": census_mod.skin_cost(lineages, set(targets), repo)}
    store = _store_or_none(args)
    if store is not None:
        out["authorship"] = census_mod.authorship_census(lineages, set(targets), store, default_cache(), blame=not args.no_blame)
    if args.json:
        print(json.dumps(out, indent=2))
        return 0
    cov, cost = out["coverage"], out["skin_cost"]
    print(f"lineages {cov['lineages']}, eras {cov['eras']}")
    print(f"character targets with a lineage: {cov['character_targets_with_lineage']} of {cov['character_targets']}")
    print(f"catalog rows (with a sheet) with a lineage: {cov['catalog_rows_with_lineage']} of {cov['catalog_rows_with_a_sheet']} {cov['catalog_rows_with_lineage_by_kind']}")
    print(f"versioned targets (<base>_vN beside <base>): {len(cov['versioned_pairs'])}; not in one lineage with their base: {len(cov['versioned_gaps'])}")
    for gap in cov["versioned_gaps"]:
        print(f"  {gap['target']} (base {gap['base']}){' — in progress, untracked' if gap['in_progress'] else ''}")
    b = cost["bytes_all_tiers"]
    print(f"published bytes per lineage target, all four tiers ({cost['targets_measured']} measured): "
          f"median {b['median'] / 1e6:.1f} MB, mean {b['mean'] / 1e6:.1f} MB, max {b['max'] / 1e6:.1f} MB")
    print(f"eras beyond one per lineage: {cost['eras_beyond_one_per_lineage']}")
    auth = out.get("authorship")
    if auth:
        print(f"eras in the history store: {auth['eras_in_store']} (missing {auth['eras_missing_from_store']})")
        print(f"commit that pins each era, by basis: {auth['pin_commit_basis']}")
        if "generator_top_author_kind" in auth:
            print(f"generator main author per era, by kind: {auth['generator_top_author_kind']}")
            print(f"generator confidence per era: {auth['generator_confidence']}; files found by: {auth['generator_found_by']}")
            for part, lines in auth["generator_lines_by_author"].items():
                print(f"{part} lines by author: " + ", ".join(f"{k} {v}" for k, v in list(lines.items())[:8]))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="design_history", description=__doc__)
    parser.add_argument("--store", help="the ambition-history store (default: sibling checkout or cache)")
    parser.add_argument("--python", help="interpreter that runs each commit's renderer")
    parser.add_argument("--keep-worktrees", action="store_true")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("fetch", help="make every history ref available").set_defaults(fn=cmd_fetch)
    sub.add_parser("list", help="the curated lineages").set_defaults(fn=cmd_list)
    p = sub.add_parser("survey", help="draw candidate commits and show the distinct looks")
    p.add_argument("lineage", nargs="*")
    p.add_argument("--all", action="store_true")
    p.add_argument("--ids", help="comma list of target ids, newest name first")
    p.add_argument("--paths", help="comma list of path regexes")
    p.add_argument("--sweep", type=int, default=0, help="also draw every N-th commit")
    p.set_defaults(fn=cmd_survey)
    p = sub.add_parser("build", help="render the curated progression sheets")
    p.add_argument("lineage", nargs="*")
    p.add_argument("--all", action="store_true")
    p.add_argument("--per-row", type=int, default=6, help="tiles per row unless a lineage sets per_row")
    p.set_defaults(fn=cmd_build)
    p = sub.add_parser("character", help="a character's lineage, eras and authorship (a catalog id, target or lineage)")
    p.add_argument("name")
    p.add_argument("--json", action="store_true")
    p.add_argument("--no-blame", action="store_true", help="skip the generator authorship (git blame)")
    p.set_defaults(fn=cmd_character)
    p = sub.add_parser("census", help="lineage coverage of the cast, era authorship and sheet cost")
    p.add_argument("--json", action="store_true")
    p.add_argument("--no-blame", action="store_true", help="skip the generator authorship (git blame)")
    p.set_defaults(fn=cmd_census)
    p = sub.add_parser("attribution", help="which model(s) a commit's evidence names")
    p.add_argument("commit")
    p.set_defaults(fn=cmd_attribution)
    args = parser.parse_args(argv)
    return args.fn(args)
