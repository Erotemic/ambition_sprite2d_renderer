"""How much of the cast the lineages cover, who authored each era, and what
the published sheets of each generation cost.

    python -m design_history census [--json] [--no-blame]

Each number names its population. The coverage half needs only this checkout
(the renderer registry, `lineages.yaml` and the game data). The authorship half
needs the history store (`python -m design_history fetch`): an era whose
commit is not in the store is counted as `missing`.
"""

from __future__ import annotations

import collections
import json
import statistics
import subprocess
import sys
from pathlib import Path

from . import characters
from .attribution import attribute
from .authorship import Blamer, era_generator
from .store import commit_info, git, load_ledger

RENDERER = Path(__file__).resolve().parents[1]
TIERS = ("sprites", "sprites_0_5x", "sprites_0_25x", "sprites_potato")


def registry(python: str | None = None) -> dict[str, dict]:
    """The renderer's own registry (`list --json`), run as a separate process
    so that nothing here imports the renderer."""
    done = subprocess.run(
        [python or sys.executable, "-m", "ambition_sprite2d_renderer", "list", "--json"],
        cwd=RENDERER, capture_output=True, text=True,
    )
    if done.returncode != 0:
        raise SystemExit(f"`ambition_sprite2d_renderer list --json` failed: {done.stderr.strip()[-300:]}")
    return json.loads(done.stdout).get("targets", {})


def untracked(paths: list[str]) -> set[str]:
    """The renderer-relative `paths` that git does not track (work in progress)."""
    if not paths:
        return set()
    done = subprocess.run(["git", "-C", str(RENDERER), "ls-files", "--", *paths], capture_output=True, text=True)
    tracked = set(done.stdout.split())
    return {p for p in paths if p not in tracked}


def coverage(lineages: dict, targets: dict[str, dict], repo: Path) -> dict:
    """Which character targets and catalog rows a lineage claims."""
    j = characters.join(lineages, repo)
    chars = {k for k, v in targets.items() if v.get("category") == "characters"}
    claimed = chars & set(j.targets)
    rows = {i: r for i, r in j.rows.items() if j.row_targets.get(i)}
    rows_claimed = {i for i in rows if j.find(i)}
    pairs = []
    prefix = "tools/ambition_sprite2d_renderer/"
    sources = {t: (targets[t].get("source") or "").removeprefix(prefix) for t in chars}
    wip = untracked([s for s in sources.values() if s])
    for new, old in characters.versioned_pairs(chars):
        pairs.append({
            "target": new, "base": old,
            "lineage": j.targets.get(new, []), "base_lineage": j.targets.get(old, []),
            "in_progress": sources.get(new) in wip,
        })
    return {
        "lineages": len(lineages),
        "eras": sum(len(s.get("eras") or []) for s in lineages.values()),
        "character_targets": len(chars),
        "character_targets_with_lineage": len(claimed),
        "lineage_ids_not_current_targets": sorted(set(j.targets) - set(targets)),
        "catalog_rows_with_a_sheet": len(rows),
        "catalog_rows_with_lineage": len(rows_claimed),
        "catalog_rows_with_lineage_by_kind": dict(collections.Counter(rows[i].kind for i in rows_claimed)),
        "versioned_pairs": pairs,
        "versioned_gaps": [p for p in pairs if not (p["lineage"] and set(p["lineage"]) & set(p["base_lineage"]))],
    }


def authorship_census(lineages: dict, current: set[str], store: Path, cache: Path | None, *, blame: bool = True) -> dict:
    """Per era: who made the commit that pins it, and who wrote the lines of
    its generator at that commit."""
    ledger = load_ledger(store)
    blamer = Blamer(store, cache, ledger)
    pin_basis: collections.Counter = collections.Counter()
    top_kind = {"code": collections.Counter(), "art": collections.Counter()}
    confidence: collections.Counter = collections.Counter()
    found_by: collections.Counter = collections.Counter()
    lines_by_author = {"code": collections.Counter(), "art": collections.Counter()}
    pin_models: collections.Counter = collections.Counter()
    rows = []
    missing = 0
    for name, spec in lineages.items():
        for era in spec.get("eras") or []:
            sha = git(store, "rev-parse", "--verify", "-q", f"{era['commit']}^{{commit}}", check=False).strip()
            if not sha:
                missing += 1
                continue
            pin = attribute(commit_info(store, sha), ledger)
            pin_basis[pin.basis] += 1
            pin_models.update(pin.models)
            row = {"lineage": name, "commit": sha[:12], "label": era["label"], "pin": {"models": list(pin.models), "basis": pin.basis}}
            if blame:
                target, files, how = era_generator(store, sha, blamer.prefix(sha) or "", spec, era, current)
                who = blamer.authorship(sha, files, how)
                confidence[who.confidence()] += 1
                found_by[who.found_by] += 1
                for part, shares in who.parts.items():
                    top_kind[part][shares[0].kind if shares else "none"] += 1
                    for share in shares:
                        lines_by_author[part][share.who] += share.lines
                row["target"] = target
                row["generator"] = who.as_dict()
            rows.append(row)
    out = {
        "eras_in_store": len(rows),
        "eras_missing_from_store": missing,
        "pin_commit_basis": dict(pin_basis),
        "pin_commit_models": dict(pin_models.most_common()),
        "eras": rows,
    }
    if blame:
        # Per era, the kind of the author with the most lines, for the code
        # (configs, modules, rigs) and for the art (the SVG drawings) apart:
        # an SVG is many lines, so one sum would let the drawings outvote the code.
        out["generator_top_author_kind"] = {k: dict(v) for k, v in top_kind.items()}
        out["generator_confidence"] = dict(confidence)
        out["generator_found_by"] = dict(found_by)
        out["generator_lines_by_author"] = {k: dict(v.most_common()) for k, v in lines_by_author.items()}
    return out


def sheet_bytes(repo: Path, target: str) -> dict[str, int] | None:
    """Bytes of `target`'s published files in each quality tier, from its
    provenance record (the full tier) and the same paths in the tier roots.
    None when the target has no record."""
    record_path = repo / "crates" / "ambition_platformer2d_actor_monolith" / "asset_provenance" / "sprites" / f"{target}.json"
    if not record_path.is_file():
        return None
    record = json.loads(record_path.read_text(encoding="utf-8"))
    assets = characters.asset_root(repo)
    out = {}
    for tier in TIERS:
        total = 0
        for row in record.get("outputs", []):
            path = assets / tier / row["path"]
            if path.is_file():
                total += path.stat().st_size
        out[tier] = total
    return out


def skin_cost(lineages: dict, current: set[str], repo: Path) -> dict:
    """What a generation costs as a runtime skin: the published bytes of each
    lineage's current targets, all tiers (Android packages every tier)."""
    per: dict[str, dict[str, int]] = {}
    for spec in lineages.values():
        for target in characters.lineage_targets(spec):
            if target in current and target not in per:
                cost = sheet_bytes(repo, target)
                if cost is not None:
                    per[target] = cost
    totals = sorted(sum(c.values()) for c in per.values())
    eras = sum(len(s.get("eras") or []) for s in lineages.values())
    published = len(per)
    return {
        "targets_measured": published,
        "bytes_all_tiers": {"median": int(statistics.median(totals)) if totals else 0,
                            "mean": int(statistics.fmean(totals)) if totals else 0,
                            "max": max(totals) if totals else 0,
                            "sum": sum(totals)},
        "bytes_by_tier_sum": {t: sum(c[t] for c in per.values()) for t in TIERS},
        "eras": eras,
        "eras_beyond_one_per_lineage": eras - sum(1 for s in lineages.values() if s.get("eras")),
        "per_target": per,
    }
