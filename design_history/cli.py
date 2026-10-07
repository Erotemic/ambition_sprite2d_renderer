"""``python -m design_history`` — run from ``tools/ambition_sprite2d_renderer``."""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import sys
from pathlib import Path

import yaml

from . import survey as survey_mod
from .attribution import attribute
from .progression import Tile, compose, stack
from .store import (
    SEGMENTS, commit_info, default_store, fetch, git, load_ledger,
)
from .stills import Worktrees, default_cache, still_for

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
                who = attribute(cand.commit, ledger).label()
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
                compose(f"{name} — survey", tiles, per_row=spec.get("per_row", 6), tile_w=spec.get("tile_w", 190)).save(OUT / "survey" / f"{name}.png")
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
                ids = [era["id"]] if era.get("id") else spec.get("ids", [name])
                still = still_for(
                    python=_python(args), worktrees=worktrees, cache=cache,
                    seg=seg, sha=commit.sha, target_ids=ids,
                    pick=era.get("pick", spec.get("pick")),
                )
                who = attribute(commit, ledger)
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
    who = attribute(commit, ledger)
    print(json.dumps({"commit": commit.sha, "date": commit.date, "models": who.models,
                      "basis": who.basis, "note": who.note}, indent=2))
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
    p = sub.add_parser("attribution", help="which model(s) a commit's evidence names")
    p.add_argument("commit")
    p.set_defaults(fn=cmd_attribution)
    args = parser.parse_args(argv)
    return args.fn(args)
