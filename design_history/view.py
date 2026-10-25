"""One character's lineage as a record: each era with its commit, the target
that draws it, who made the commit, who wrote its generator, and its still if
the cache has one. The `character` command prints it and the art inspector
shows it on an asset page."""

from __future__ import annotations

from pathlib import Path

from .attribution import attribute
from .authorship import Blamer, era_generator
from .characters import era_ids, lineage_targets
from .stills import cached_still
from .store import commit_info, git


def lineage_view(
    name: str, spec: dict, *, store: Path | None, cache: Path | None, blamer: Blamer | None,
    current: set[str], ledger: dict | None = None,
) -> dict:
    """The record of lineage `name`. With no `store`, or an era commit that is
    not in it, the era keeps its commit and label only (`in_store: false`).
    With no `blamer`, no generator authorship is measured."""
    eras = []
    for era in spec.get("eras") or []:
        row = {
            "commit": str(era["commit"]),
            "label": era.get("label", ""),
            "note": era.get("note", ""),
            "ids": era_ids(name, spec, era),
            "in_store": False,
        }
        sha = git(store, "rev-parse", "--verify", "-q", f"{era['commit']}^{{commit}}", check=False).strip() if store else ""
        if sha:
            info = commit_info(store, sha)
            pin = attribute(info, ledger or {})
            row.update({
                "in_store": True,
                "sha": sha,
                "date": info.date,
                "subject": info.subject,
                "pin": {"models": list(pin.models), "basis": pin.basis, "note": pin.note, "label": pin.label()},
            })
            if blamer is not None:
                target, files, how = era_generator(store, sha, blamer.prefix(sha) or "", spec, era, current)
                row["target"] = target
                row["generator"] = blamer.authorship(sha, files, how).as_dict()
            if cache is not None:
                still = cached_still(cache, sha, row["ids"], era.get("pick", spec.get("pick")))
                row["still"] = str(still) if still else None
        eras.append(row)
    return {
        "lineage": name,
        "name": spec.get("name", name),
        "summary": spec.get("summary", ""),
        "targets": lineage_targets(spec),
        "current_targets": [t for t in lineage_targets(spec) if t in current],
        "eras": eras,
    }
